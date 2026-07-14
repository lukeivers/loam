# Pending delta — claude-code-hooks

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/hooks`
> Projection target: `claude-code/hooks.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-14T12:59:59Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Reference Hooks reference Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Hook lifecycle How a hook resolves Configuration Hook locations Matcher patterns Match MCP tools Hook handler fields Common fields Command hook fields HTTP hook fields MCP tool hook fields Prompt and agent hook fields Reference scripts by path Hooks in skills and agents The /hooks menu Disable or remove hooks Hook input and output Common input fields Exit code output Exit code 2 behavior per event HTTP response handling JSON output Emit terminal notifications Add context for Claude Decision control Hook events SessionStart SessionStart input SessionStart decision control Persist environment variables Setup Setup input Setup decision control InstructionsLoaded InstructionsLoaded input InstructionsLoaded decision control UserPromptSubmit UserPromptSubmit input UserPromptSubmit decision control UserPromptExpansion UserPromptExpansion input UserPromptExpansion decision control MessageDisplay MessageDisplay input MessageDisplay output PreToolUse PreToolUse input PreToolUse decision control Defer a tool call for later PermissionRequest PermissionRequest input PermissionRequest decision control Permission update entries PostToolUse PostToolUse input PostToolUse decision control PostToolUseFailure PostToolUseFailure input PostToolUseFailure decision control PostToolBatch PostToolBatch input PostToolBatch decision control PermissionDenied PermissionDenied input PermissionDenied decision control Notification Notification input SubagentStart SubagentStart input SubagentStop SubagentStop input TaskCreated TaskCreated input TaskCreated decision control TaskCompleted TaskCompleted input TaskCompleted decision control Stop Stop input Stop decision control StopFailure StopFailure input TeammateIdle TeammateIdle input TeammateIdle decision control ConfigChange ConfigChange input ConfigChange decision control CwdChanged CwdChanged input CwdChanged output FileChanged FileChanged input FileChanged output WorktreeCreate WorktreeCreate input WorktreeCreate output WorktreeRemove WorktreeRemove input PreCompact PreCompact input PostCompact PostCompact input SessionEnd SessionEnd input Elicitation Elicitation input Elicitation output ElicitationResult ElicitationResult input ElicitationResult output Prompt-based hooks How prompt-based hooks work Prompt hook configuration Response schema Example: Multi-criteria Stop hook Agent-based hooks How agent hooks work Agent hook configuration Run hooks in the background Configure an async hook How async hooks execute Example: run tests after file changes Limitations Security considerations Disclaimer Security best practices Windows PowerShell tool Debug hooks Reference Hooks reference Copy page Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, HTTP hooks, prompt hooks, and MCP tool hooks.
  - now: Navigation Reference Hooks reference Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Hook lifecycle How a hook resolves Configuration Hook locations Matcher patterns Match MCP tools Hook handler fields Common fields Command hook fields HTTP hook fields MCP tool hook fields Prompt and agent hook fields Reference scripts by path Hooks in skills and agents The /hooks menu Disable or remove hooks Hook input and output Common input fields Exit code output Exit code 2 behavior per event HTTP response handling JSON output Emit terminal notifications Add context for Claude Decision control Hook events SessionStart SessionStart input SessionStart decision control Persist environment variables Setup Setup input Setup decision control InstructionsLoaded InstructionsLoaded input InstructionsLoaded decision control UserPromptSubmit UserPromptSubmit input UserPromptSubmit decision control UserPromptExpansion UserPromptExpansion input UserPromptExpansion decision control MessageDisplay MessageDisplay input MessageDisplay output PreToolUse PreToolUse input PreToolUse decision control Defer a tool call for later PermissionRequest PermissionRequest input PermissionRequest decision control Permission update entries PostToolUse PostToolUse input PostToolUse decision control PostToolUseFailure PostToolUseFailure input PostToolUseFailure decision control PostToolBatch PostToolBatch input PostToolBatch decision control PermissionDenied PermissionDenied input PermissionDenied decision control Notification Notification input SubagentStart SubagentStart input SubagentStop SubagentStop input TaskCreated TaskCreated input TaskCreated decision control TaskCompleted TaskCompleted input TaskCompleted decision control Stop Stop input Stop decision control StopFailure StopFailure input TeammateIdle TeammateIdle input TeammateIdle decision control ConfigChange ConfigChange input ConfigChange decision control CwdChanged CwdChanged input CwdChanged output FileChanged FileChanged input FileChanged output WorktreeCreate WorktreeCreate input WorktreeCreate output WorktreeRemove WorktreeRemove input PreCompact PreCompact input PostCompact PostCompact input SessionEnd SessionEnd input Elicitation Elicitation input Elicitation output ElicitationResult ElicitationResult input ElicitationResult output Prompt-based hooks How prompt-based hooks work Prompt hook configuration Response schema Check multiple conditions before stopping Agent-based hooks How agent hooks work Agent hook configuration Run hooks in the background Configure an async hook How async hooks execute Run tests after file changes Limitations Security considerations Disclaimer Security best practices Windows PowerShell tool Debug hooks Reference Hooks reference Copy page Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, HTTP hooks, prompt hooks, and MCP tool hooks.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Events fall into three cadences: once per session ( SessionStart , SessionEnd ), once per turn ( UserPromptSubmit , Stop , StopFailure ), and on every tool call inside the agentic loop ( PreToolUse , PostToolUse ): The table below summarizes when each event fires.
  - now: Events fall into three cadences: once per session: SessionStart and SessionEnd once per turn: UserPromptSubmit , Stop , and StopFailure on every tool call inside the agentic loop: PreToolUse and PostToolUse The table below summarizes when each event fires.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The FileChanged event does not follow these rules when building its watch list.
  - now: The FileChanged event doesn’t follow these rules when building its watch list.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Each event type matches on a different field: Event What the matcher filters Example matcher values PreToolUse , PostToolUse , PostToolUseFailure , PermissionRequest , PermissionDenied tool name Bash , Edit|Write , mcp__.* SessionStart how the session started startup , resume , clear , compact Setup which CLI flag triggered setup init , maintenance SessionEnd why the session ended clear , resume , logout , prompt_input_exit , bypass_permissions_disabled , other Notification notification type permission_prompt , idle_prompt , auth_success , elicitation_dialog , elicitation_complete , elicitation_response SubagentStart agent type general-purpose , Explore , Plan , custom agent names, or plugin-scoped names like ^my-plugin:reviewer$ PreCompact , PostCompact what triggered compaction manual , auto SubagentStop agent type same values as SubagentStart ConfigChange configuration source user_settings , project_settings , local_settings , policy_settings , skills CwdChanged no matcher support always fires on every directory change FileChanged literal filenames to watch (see FileChanged ) .envrc|.env StopFailure error type rate_limit , overloaded , authentication_failed , oauth_org_not_allowed , billing_error , invalid_request , model_not_found , server_error , max_output_tokens , unknown InstructionsLoaded load reason session_start , nested_traversal , path_glob_match , include , compact UserPromptExpansion command name your skill or command names Elicitation MCP server name your configured MCP server names ElicitationResult MCP server name same values as Elicitation UserPromptSubmit , PostToolBatch , Stop , TeammateIdle , TaskCreated , TaskCompleted , WorktreeCreate , WorktreeRemove , MessageDisplay no matcher support always fires on every occurrence The matcher runs against a field from the JSON input that Claude Code sends to your hook on stdin.
  - now: Each event type matches on a different field: Event What the matcher filters Example matcher values PreToolUse , PostToolUse , PostToolUseFailure , PermissionRequest , PermissionDenied tool name Bash , Edit|Write , mcp__.* SessionStart how the session started startup , resume , clear , compact Setup which CLI flag triggered setup init , maintenance SessionEnd why the session ended clear , resume , logout , prompt_input_exit , bypass_permissions_disabled , other Notification notification type permission_prompt , idle_prompt , auth_success , elicitation_dialog , elicitation_complete , elicitation_response , agent_needs_input , agent_completed SubagentStart agent type general-purpose , Explore , Plan , custom agent names, or plugin-scoped names like ^my-plugin:reviewer$ PreCompact , PostCompact what triggered compaction manual , auto SubagentStop agent type same values as SubagentStart ConfigChange configuration source user_settings , project_settings , local_settings , policy_settings , skills CwdChanged no matcher support always fires on every directory change FileChanged literal filenames to watch (see FileChanged ) .envrc|.env StopFailure error type rate_limit , overloaded , authentication_failed , oauth_org_not_allowed , billing_error , invalid_request , model_not_found , server_error , max_output_tokens , unknown InstructionsLoaded load reason session_start , nested_traversal , path_glob_match , include , compact UserPromptExpansion command name your skill or command names Elicitation MCP server name your configured MCP server names ElicitationResult MCP server name same values as Elicitation UserPromptSubmit , PostToolBatch , Stop , TeammateIdle , TaskCreated , TaskCompleted , WorktreeCreate , WorktreeRemove , MessageDisplay no matcher support always fires on every occurrence The matcher runs against a field from the JSON input that Claude Code sends to your hook on stdin.
- **new-claim** — adds a capability claim not previously upstream
  - now: Tools from a plugin-bundled MCP server use a scoped server segment that includes the plugin name: mcp__plugin_<plugin-name>_<server-name>__<tool> .
A matcher written against the bare server key never fires for these tools.
For a plugin named my-plugin that bundles a server under the key db , a query tool appears as mcp__plugin_my-plugin_db__query , so the matcher for every tool from that server is mcp__plugin_my-plugin_db__.* .
Use the same scoped tool name in a handler’s if field .
See Plugin-provided MCP servers for how the scoped name is built.
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.199, $CLAUDE_CODE_BRIDGE_SESSION_ID is set to the Remote Control session ID while the local session has an active Remote Control connection.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Why Bash(git *) FOO=bar git push yes leading assignments are stripped; git push matches Bash(git *) npm test && git push yes each subcommand is checked; git push matches Bash(rm *) echo $(rm -rf /) yes commands inside $() and backticks are checked; rm -rf / matches Bash(rm *) echo $(date) no no subcommand matches rm * Bash(git push *) echo $(date) yes patterns that specify more than the command name run the hook anyway on $() , backticks, or $VAR The filter also fails open, running your hook regardless of pattern, when the Bash command cannot be parsed.
  - now: Why Bash(git *) FOO=bar git push yes leading assignments are stripped; git push matches Bash(git *) npm test && git push yes each subcommand is checked; git push matches Bash(rm *) echo $(rm -rf /) yes commands inside $() and backticks are checked; rm -rf / matches Bash(rm *) echo $(date) no no subcommand matches rm * Bash(git push *) echo $(date) yes patterns that specify more than the command name run the hook anyway on $() , backticks, or $VAR The filter also fails open, running your hook regardless of pattern, when the Bash command can’t be parsed.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The .cmd and .bat shims that npm, npx, eslint, and other tools install in node_modules/.bin are not executables and cannot be spawned without a shell.
  - now: The .cmd and .bat shims that npm, npx, eslint, and other tools install in node_modules/.bin are not executables and can’t be spawned without a shell.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Plugin hooks additionally substitute ${user_config.*} values; see User configuration .
  - now: Plugin hooks additionally substitute ${user_config.*} values, in exec form only: the value is substituted into command and into each args element as a plain string, so no shell re-parses it.
A shell-form plugin hook whose command references ${user_config.*} fails with an error instead of running.
To use an option value from a shell-form hook, read the $CLAUDE_PLUGIN_OPTION_<KEY> environment variable, such as $CLAUDE_PLUGIN_OPTION_WEBHOOK_URL for a webhook_url option, or set args to switch the hook to exec form.
Before v2.1.207, shell-form plugin hook commands also substituted ${user_config.*} .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Absolute paths with spaces, such as C:\Program Files\nodejs\node.exe , are a single valid executable and do not trigger the warning.
  - now: Absolute paths with spaces, such as C:\Program Files\nodejs\node.exe , are a single valid executable and don’t trigger the warning.
- **new-claim** — adds a capability claim not previously upstream
  - now: For a plugin-bundled server , this is the scoped name plugin:<plugin-name>:<server-name> , such as plugin:my-plugin:db , not the bare server key.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: If an administrator has configured hooks through managed policy settings, disableAllHooks set in user, project, or local settings cannot disable those managed hooks.
  - now: If an administrator has configured hooks through managed policy settings, disableAllHooks set in user, project, or local settings can’t disable those managed hooks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The hook process and any child processes cannot open /dev/tty or send escape sequences directly to the Claude Code interface.
  - now: The hook process and any child processes can’t open /dev/tty or send escape sequences directly to the Claude Code interface.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Requires Claude Code v2.1.196 or later transcript_path Path to conversation JSON cwd Current working directory when the hook is invoked permission_mode Current permission mode : "default" , "plan" , "acceptEdits" , "auto" , "dontAsk" , or "bypassPermissions" .
Not all events receive this field: see each event’s JSON example below to check effort Object with a level field holding the active effort level for the turn: "low" , "medium" , "high" , "xhigh" , or "max" .
  - now: Requires Claude Code v2.1.196 or later transcript_path Path to conversation JSON.
The transcript file is written asynchronously and may lag the in-memory conversation, so it may not yet include the current turn’s most recent messages when a hook fires.
Hooks that need the final assistant text of the current turn should use last_assistant_message on Stop and SubagentStop instead of reading the transcript cwd Current working directory when the hook is invoked permission_mode Current permission mode : "default" , "plan" , "acceptEdits" , "auto" , "dontAsk" , or "bypassPermissions" .
The mode labeled Manual arrives as "default" , never as "manual" , so scripts that match "default" keep working.
Not all events receive this field.
Check the JSON example in each hook event section effort Object with a level field holding the active effort level for the turn: "low" , "medium" , "high" , "xhigh" , or "max" .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: A hook process inherits the parent environment, so it can read $ANTHROPIC_MODEL if you set it in your shell, but that value does not change when you switch models with /model during a session.
  - now: A hook process inherits the parent environment, so it can read $ANTHROPIC_MODEL if you set it in your shell, but that value doesn’t change when you switch models with /model during a session.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: What happens on exit 2 PreToolUse Yes Blocks the tool call PermissionRequest Yes Denies the permission UserPromptSubmit Yes Blocks prompt processing and erases the prompt UserPromptExpansion Yes Blocks the expansion Stop Yes Prevents Claude from stopping, continues the conversation SubagentStop Yes Prevents the subagent from stopping TeammateIdle Yes Prevents the teammate from going idle (teammate continues working) TaskCreated Yes Rolls back the task creation TaskCompleted Yes Prevents the task from being marked as completed ConfigChange Yes Blocks the configuration change from taking effect (except policy_settings ) StopFailure No Output and exit code are ignored PostToolUse No Shows stderr to Claude (tool already ran) PostToolUseFailure No Shows stderr to Claude (tool already failed) PostToolBatch Yes Stops the agentic loop before the next model call PermissionDenied No Exit code and stderr are ignored (denial already occurred).
Use JSON hookSpecificOutput.retry: true to tell the model it may retry Notification No Shows stderr to user only SubagentStart No Shows stderr to user only SessionStart No Shows stderr to user only Setup No Shows stderr to user only SessionEnd No Shows stderr to user only CwdChanged No Shows stderr to user only FileChanged No Shows stderr to user only PreCompact Yes Blocks compaction PostCompact No Shows stderr to user only Elicitation Yes Denies the elicitation ElicitationResult Yes Blocks the response (action becomes decline) WorktreeCreate Yes Any non-zero exit code causes worktree creation to fail WorktreeRemove No Failures are logged in debug mode only InstructionsLoaded No Exit code is ignored MessageDisplay No The original text is displayed ​ HTTP response handling HTTP hooks use HTTP status codes and response bodies instead of exit codes and stdout: 2xx with an empty body : success, equivalent to exit code 0 with no output 2xx with a plain text body : success, the text is added as context 2xx with a JSON body : success, parsed using the same JSON output schema as command hooks Non-2xx status : non-blocking error, execution continues Connection failure or timeout : non-blocking error, execution continues Unlike command hooks, HTTP hooks cannot signal a blocking error through status codes alone.
  - now: What happens on exit 2 PreToolUse Yes Blocks the tool call PermissionRequest Yes Denies the permission UserPromptSubmit Yes Blocks prompt processing and erases the prompt UserPromptExpansion Yes Blocks the expansion Stop Yes Prevents Claude from stopping, continues the conversation SubagentStop Yes Prevents the subagent from stopping TeammateIdle Yes Prevents the teammate from going idle, so it continues working TaskCreated Yes Rolls back the task creation TaskCompleted Yes Prevents the task from being marked as completed ConfigChange Yes Blocks the configuration change from taking effect (except policy_settings ) StopFailure No Output and exit code are ignored PostToolUse No Shows stderr to Claude; the tool already ran PostToolUseFailure No Shows stderr to Claude; the tool already failed PostToolBatch Yes Stops the agentic loop before the next model call PermissionDenied No Exit code and stderr are ignored because the denial already occurred.
Use JSON hookSpecificOutput.retry: true to tell the model it may retry Notification No Shows stderr to user only SubagentStart No Shows stderr to user only SessionStart No Shows stderr to user only Setup No Shows stderr to user only SessionEnd No Shows stderr to user only CwdChanged No Shows stderr to user only FileChanged No Shows stderr to user only PreCompact Yes Blocks compaction PostCompact No Shows stderr to user only Elicitation Yes Denies the elicitation ElicitationResult Yes Blocks the response (action becomes decline) WorktreeCreate Yes Any non-zero exit code causes worktree creation to fail WorktreeRemove No Failures are logged in debug mode only InstructionsLoaded No Exit code is ignored MessageDisplay No The original text is displayed For SessionStart , Setup , and SubagentStart , the exit code 2 stderr renders in the transcript as a <hook name> hook error notice, the same way a non-blocking error does.
Claude doesn’t see it, and the session or subagent proceeds.
For SubagentStart , the notice appears in the subagent’s own transcript, not in the parent conversation.
As of Claude Code v2.1.199, SessionStart , Setup , and SubagentStart show exit code 2 stderr in the transcript.
Earlier versions wrote it to the debug log only.
​ HTTP response handling HTTP hooks use HTTP status codes and response bodies instead of exit codes and stdout: 2xx with an empty body : success, equivalent to exit code 0 with no output 2xx with a plain text body : success, the text is added as context 2xx with a JSON body : success, parsed using the same JSON output schema as command hooks Non-2xx status : non-blocking error, execution continues Connection failure or timeout : non-blocking error, execution continues Unlike command hooks, HTTP hooks can’t signal a blocking error through status codes alone.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The allowlist is restricted to sequences that cannot move the cursor or alter colors, so a hook can never corrupt an on-screen prompt.
  - now: The allowlist is restricted to sequences that can’t move the cursor or alter colors, so a hook can never corrupt an on-screen prompt.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Claude reads the reminder on the next model request, but it does not appear as a chat message in the interface.
  - now: Claude reads the reminder on the next model request, but it doesn’t appear as a chat message in the interface.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: See PostToolUse decision control UserPromptSubmit : cannot replace the prompt; it only injects additionalContext alongside it For redaction or transformation use cases, intercept at PreToolUse for outbound tool inputs and PostToolUse for inbound tool results.
  - now: See PostToolUse decision control UserPromptSubmit : can’t replace the prompt; it only injects additionalContext alongside it For redaction or transformation use cases, intercept at PreToolUse for outbound tool inputs and PostToolUse for inbound tool results.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For static context that does not require a script, use CLAUDE.md instead.
  - now: For static context that doesn’t require a script, use CLAUDE.md instead.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The matcher value corresponds to how the session was initiated: Matcher When it fires startup New session resume --resume , --continue , or /resume clear /clear compact Auto or manual compaction ​ SessionStart input In addition to the common input fields , SessionStart hooks receive source and optionally model , agent_type , and session_title .
The source field indicates how the session started: "startup" for new sessions, "resume" for resumed sessions, "clear" after /clear , or "compact" after compaction.
The model field contains the active model identifier.
It can be omitted, for example after /clear or when a session is restored through conversation recovery, so check for the field before reading it.
If you start Claude Code with claude --agent <name> , an agent_type field contains the agent name.
The session_title field carries the current session title if one is already set, for example via --name or /rename .
A hook that emits sessionTitle can check session_title first to avoid overwriting a title the user set explicitly.
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SessionStart" , "source" : "startup" , "model" : "claude-sonnet-5" } ​ SessionStart decision control Any text your hook script prints to stdout is added as context for Claude.
  - now: The matcher value corresponds to how the session was initiated: Matcher When it fires startup New session resume --resume , --continue , or /resume clear /clear compact Auto or manual compaction ​ SessionStart input In addition to the common input fields , SessionStart hooks receive source and optionally model , agent_type , and session_title : Field Description source How the session started: "startup" for new sessions, "resume" for resumed sessions, "clear" after /clear , or "compact" after compaction model The active model identifier.
It can be omitted, for example after /clear or when a session is restored through conversation recovery, so check for the field before reading it agent_type The agent name, present when you start Claude Code with claude --agent <name> session_title The current session title if one is already set, for example via --name or /rename .
A hook that emits sessionTitle can check session_title first to avoid overwriting a title the user set explicitly { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SessionStart" , "source" : "startup" , "model" : "claude-sonnet-5" } ​ SessionStart decision control Any text your hook script prints to stdout is added as context for Claude.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Applies in non-interactive mode ( -p ), where it becomes the first turn even if no prompt is provided.
  - now: Applies in non-interactive mode with the -p flag, where it becomes the first turn even if no prompt is provided.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Other hook types do not have access to this variable.
​ Setup Fires only when you launch Claude Code with --init-only , or with --init or --maintenance in print mode ( -p ).
It does not fire on normal startup.
  - now: Other hook types don’t have access to this variable.
​ Setup Fires only when you launch Claude Code with --init-only , or with --init or --maintenance in non-interactive mode with the -p flag.
It doesn’t fire on normal startup.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: --init and --maintenance fire Setup hooks only when combined with -p (print mode); in an interactive session those two flags do not currently fire Setup hooks.
Because Setup does not fire on every launch, a plugin that needs a dependency installed cannot rely on Setup alone.
  - now: --init and --maintenance fire Setup hooks only when combined with -p ; in an interactive session those two flags don’t currently fire Setup hooks.
Because Setup doesn’t fire on every launch, a plugin that needs a dependency installed can’t rely on Setup alone.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Setup input In addition to the common input fields , Setup hooks receive a trigger field set to either "init" or "maintenance" : { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Setup" , "trigger" : "init" } ​ Setup decision control Setup hooks cannot block.
On exit code 2, stderr is shown to the user; on any other non-zero exit code, stderr appears only when you launch with --verbose .
In both cases execution continues.
  - now: ​ Setup input In addition to the common input fields , Setup hooks receive a trigger field set to either "init" or "maintenance" : { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Setup" , "trigger" : "init" } ​ Setup decision control Setup hooks can’t block.
Any non-zero exit code, including 2, surfaces stderr to the user as a <hook name> hook error notice, and execution continues.
In non-interactive mode , hook output appears only when you launch with --verbose .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The hook does not support blocking or decision control.
  - now: The hook doesn’t support blocking or decision control.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block or modify instruction loading.
  - now: They can’t block or modify instruction loading.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The additionalContext field is added more discretely.
  - now: The additionalContext value is injected as a system reminder that Claude reads without a visible transcript entry.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use to name sessions automatically based on the prompt content suppressOriginalPrompt If true when decision is "block" , omits the original prompt text from the block message shown to the user { "decision" : "block" , "reason" : "Explanation for decision" , "hookSpecificOutput" : { "hookEventName" : "UserPromptSubmit" , "additionalContext" : "My additional context here" , "sessionTitle" : "My session title" } } The JSON format isn’t required for simple use cases.
To add context, you can print plain text to stdout with exit code 0.
Use JSON when you need to block prompts or want more structured control.
​ UserPromptExpansion Runs when a user-typed slash command expands into a prompt before reaching Claude.
  - now: Use to name sessions automatically based on the prompt content suppressOriginalPrompt If true when decision is "block" , omits the original prompt text from the block message shown to the user { "decision" : "block" , "reason" : "Explanation for decision" , "hookSpecificOutput" : { "hookEventName" : "UserPromptSubmit" , "additionalContext" : "My additional context here" , "sessionTitle" : "My session title" } } ​ UserPromptExpansion Runs when a user-typed command expands into a prompt before reaching Claude.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This event covers the path PreToolUse does not: a PreToolUse hook matching the Skill tool fires only when Claude calls the tool, but typing /skillname directly bypasses PreToolUse .
  - now: This event covers the path PreToolUse doesn’t: a PreToolUse hook matching the Skill tool fires only when Claude calls the tool, but typing /skillname directly bypasses PreToolUse .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Leave the matcher empty to fire on every prompt-type slash command.
  - now: Leave the matcher empty to fire on every prompt-type command.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Field Description decision "block" prevents the slash command from expanding.
  - now: Field Description decision "block" prevents the command from expanding.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: MessageDisplay does not support matchers and fires for every assistant message that streams text; messages with no text, such as tool-call-only responses, do not trigger it.
  - now: MessageDisplay doesn’t support matchers and fires for every assistant message that streams text; messages with no text, such as tool-call-only responses, don’t trigger it.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This is not the API msg_… id, so it cannot be correlated with transcript message ids index Zero-based index of this batch within the message final true on the message’s last batch.
  - now: This is not the API msg_… id, so it can’t be correlated with transcript message ids index Zero-based index of this batch within the message final true on the message’s last batch.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block the message or change what is stored in the transcript or sent to Claude.
  - now: They can’t block the message or change what is stored in the transcript or sent to Claude.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Read these fields to record per-subagent cost from a hook: Field Type Example Description status string "completed" "completed" for synchronous calls, "async_launched" for run_in_background: true agentId string "a4d2c8f1e0b3a297" Identifier for the subagent run content array [{"type": "text", "text": "Found 12 endpoints..."}] The subagent’s final text blocks resolvedModel string "claude-sonnet-4-5" Model the subagent ran on, which may differ from the requested model.
Requires Claude Code v2.1.174 or later totalTokens number 12450 Total tokens billed across the subagent’s turns totalDurationMs number 48211 Wall-clock duration of the subagent run totalToolUseCount number 7 Count of tool calls the subagent made usage object {"input_tokens": 8320, ...} Per-type token breakdown: input_tokens , output_tokens , cache_creation_input_tokens , cache_read_input_tokens For run_in_background: true calls, the tool returns immediately after launching the subagent, so tool_response carries no usage fields.
  - now: Read these fields to record per-subagent cost from a hook: Field Type Example Description status string "completed" "completed" for foreground subagents, "async_launched" for background subagents.
As of v2.1.198, subagents run in the background by default, so an omitted run_in_background also produces "async_launched" agentId string "a4d2c8f1e0b3a297" Identifier for the subagent run content array [{"type": "text", "text": "Found 12 endpoints..."}] The subagent’s final text blocks resolvedModel string "claude-sonnet-4-5" Model the subagent ran on, which may differ from the requested model.
Requires Claude Code v2.1.174 or later totalTokens number 12450 Total tokens billed across the subagent’s turns totalDurationMs number 48211 Wall-clock duration of the subagent run totalToolUseCount number 7 Count of tool calls the subagent made usage object {"input_tokens": 8320, ...} Per-type token breakdown: input_tokens , output_tokens , cache_creation_input_tokens , cache_read_input_tokens For background subagents, the tool returns immediately after launching, so tool_response carries no usage fields.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Claude does not set this field; supply it via updatedInput to answer programmatically ExitPlanMode Presents a plan and asks the user to approve it before Claude leaves plan mode .
Claude writes the plan to a file on disk before calling the tool, so the literal tool_input from the model only carries allowedPrompts .
  - now: Claude doesn’t set this field; supply it via updatedInput to answer programmatically ExitPlanMode Presents a plan and asks the user to approve it before Claude leaves plan mode .
Claude writes the plan to a file on disk before calling the tool, so the literal tool_input from the model is typically empty.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Injected allowedPrompts array [{"tool": "Bash", "prompt": "run tests"}] Optional.
Prompt-based permissions Claude is requesting to implement the plan, each with a tool name and a prompt describing the category of action In PostToolUse , tool_response is an object with plan and filePath fields holding the approved plan, plus internal status flags.
  - now: Injected allowedPrompts array [{"tool": "Bash", "prompt": "run tests"}] Deprecated.
Claude Code accepts the field but ignores it.
Before v2.1.205, it carried prompt-based permissions Claude requested to implement the plan In PostToolUse , tool_response is an object with plan and filePath fields holding the approved plan, plus internal status flags.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Field Description permissionDecision "allow" skips the permission prompt.
  - now: Field Description permissionDecision "allow" skips the permission prompt, except for tools that require user interaction .
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.199, an MCP tool whose server marks it with _meta["anthropic/requiresUserInteraction"] is stricter: a hook can’t skip its approval prompt with "allow" , with or without updatedInput , because Claude Code can’t confirm the hook collected the interaction the tool needs.
- **removal** — removes a previously-present capability claim
  - was: The defer value requires Claude Code v2.1.89 or later.
Earlier versions do not recognize it and the tool proceeds through the normal permission flow.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The tool does not execute.
  - now: The tool doesn’t execute.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: --resume restores the permission mode that was active when the tool was deferred, so you do not need to pass --permission-mode again.
  - now: --resume restores the permission mode that was active when the tool was deferred, so you don’t need to pass --permission-mode again.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Deny and ask rules are still evaluated, so a hook returning "allow" does not override a matching deny rule updatedInput For "allow" only: modifies the tool’s input parameters before execution.
  - now: Deny and ask rules are still evaluated, so a hook returning "allow" doesn’t override a matching deny rule updatedInput For "allow" only: modifies the tool’s input parameters before execution.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Valid modes are default , auto , acceptEdits , dontAsk , bypassPermissions , and plan addDirectories directories , destination Adds working directories.
  - now: Valid modes are default , auto , acceptEdits , dontAsk , bypassPermissions , plan , and manual as an alias for default .
The manual alias requires Claude Code v2.1.200 or later addDirectories directories , destination Adds working directories.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For built-in tools, a value that does not match the tool’s output schema is ignored and the original output is used.
  - now: For built-in tools, a value that doesn’t match the tool’s output schema is ignored and the original output is used.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ PostToolUseFailure Runs when a tool execution fails.
This event fires for tool calls that throw errors or return failure results.
  - now: ​ PostToolUseFailure Runs when a tool that started executing fails: the tool threw an error, or an MCP tool returned an error result.
- **new-claim** — adds a capability claim not previously upstream
  - now: This event doesn’t fire for tool calls rejected before execution: an unknown tool name, input that fails schema or tool-specific validation, or a permission denial.
Validation rejections are returned as tool_use_error results and happen before hooks run, so they fire neither PreToolUse nor PostToolUseFailure .
Permission denials fire PreToolUse but not this event; see PermissionDenied .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This hook only fires in auto mode: it does not run when you manually deny a permission dialog, when a PreToolUse hook blocks a call, or when a deny rule matches.
  - now: This hook only fires in auto mode: it doesn’t run when you manually deny a permission dialog, when a PreToolUse hook blocks a call, or when a deny rule matches.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: If your hook does not return JSON, or returns retry: false , the denial stands and the model receives the original rejection message.
  - now: If your hook doesn’t return JSON, or returns retry: false , the denial stands and the model receives the original rejection message.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Matches on notification type: permission_prompt , idle_prompt , auth_success , elicitation_dialog , elicitation_complete , elicitation_response .
  - now: Matches on notification type.
- **new-claim** — adds a capability claim not previously upstream
  - now: Matcher When it fires permission_prompt Claude needs you to approve a tool use idle_prompt Claude is done and waiting for your next prompt auth_success Authentication completes elicitation_dialog An MCP server opens an elicitation form elicitation_complete An MCP elicitation form is submitted or dismissed elicitation_response An MCP elicitation response is sent back to the server agent_needs_input A background session starts waiting on your input.
Fires only while agent view is open in a terminal agent_completed A background session finishes or fails.
Fires only while agent view is open in a terminal The agent_needs_input and agent_completed types require Claude Code v2.1.198 or later.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Notification" , "message" : "Claude needs your permission" , "title" : "Permission needed" , "notification_type" : "permission_prompt" } Notification hooks cannot block or modify notifications.
  - now: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Notification" , "message" : "Claude needs your permission" , "title" : "Permission needed" , "notification_type" : "permission_prompt" } Notification hooks can’t block or modify notifications.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ SubagentStart input In addition to the common input fields , SubagentStart hooks receive agent_id with the unique identifier for the subagent and agent_type with the agent name (built-in agents like "general-purpose" , "Explore" , "Plan" , or custom agent names).
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SubagentStart" , "agent_id" : "agent-abc123" , "agent_type" : "Explore" } SubagentStart hooks cannot block subagent creation, but they can inject context into the subagent.
  - now: ​ SubagentStart input In addition to the common input fields , SubagentStart hooks receive agent_id with the unique identifier for the subagent and agent_type with the agent name that the matcher filters on.
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SubagentStart" , "agent_id" : "agent-abc123" , "agent_type" : "Explore" } SubagentStart hooks can’t block subagent creation, but they can inject context into the subagent.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: TaskCreated hooks do not support matchers and fire on every occurrence.
  - now: TaskCreated hooks don’t support matchers and fire on every occurrence.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: TaskCompleted hooks do not support matchers and fire on every occurrence.
  - now: TaskCompleted hooks don’t support matchers and fire on every occurrence.
- **new-claim** — adds a capability claim not previously upstream
  - now: For hooks that act on the just-completed turn, such as read-aloud or notification hooks, use this field rather than reading transcript_path : the transcript file isn’t guaranteed to include the final message at Stop time on all versions.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use this to log failures, send alerts, or take recovery actions when Claude cannot complete a response due to rate limits, authentication problems, or other API errors.
  - now: Use this to log failures, send alerts, or take recovery actions when Claude can’t complete a response due to rate limits, authentication problems, or other API errors.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: TeammateIdle hooks do not support matchers and fire on every occurrence.
  - now: TeammateIdle hooks don’t support matchers and fire on every occurrence.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Omit to allow the change reason Explanation shown to the user when decision is "block" { "decision" : "block" , "reason" : "Configuration changes to project settings require admin approval" } policy_settings changes cannot be blocked.
  - now: Omit to allow the change reason Explanation shown to the user when decision is "block" { "decision" : "block" , "reason" : "Configuration changes to project settings require admin approval" } policy_settings changes can’t be blocked.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: CwdChanged does not support matchers and fires on every directory change.
  - now: CwdChanged doesn’t support matchers and fires on every directory change.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Replaces the current dynamic watch list (paths from your matcher configuration are always watched).
  - now: Replaces the current dynamic watch list.
Paths from your matcher configuration are always watched.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block the directory change.
  - now: They can’t block the directory change.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Field Description file_path Absolute path to the file that changed event What happened: "change" (file modified), "add" (file created), or "unlink" (file deleted) { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../transcript.jsonl" , "cwd" : "/Users/my-project" , "hook_event_name" : "FileChanged" , "file_path" : "/Users/my-project/.envrc" , "event" : "change" } ​ FileChanged output In addition to the JSON output fields available to all hooks, FileChanged hooks can return watchPaths to dynamically update which file paths are watched: Field Description watchPaths Array of absolute paths.
Replaces the current dynamic watch list (paths from your matcher configuration are always watched).
  - now: Field Description file_path Absolute path to the file that changed event What happened: "change" for a modified file, "add" for a created file, or "unlink" for a deleted file { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../transcript.jsonl" , "cwd" : "/Users/my-project" , "hook_event_name" : "FileChanged" , "file_path" : "/Users/my-project/.envrc" , "event" : "change" } ​ FileChanged output In addition to the JSON output fields available to all hooks, FileChanged hooks can return watchPaths to dynamically update which file paths are watched: Field Description watchPaths Array of absolute paths.
Replaces the current dynamic watch list.
Paths from your matcher configuration are always watched.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block the file change from occurring.
​ WorktreeCreate When you run claude --worktree or a subagent uses isolation: "worktree" , Claude Code creates an isolated working copy using git worktree .
If you configure a WorktreeCreate hook, it replaces the default git behavior, letting you use a different version control system like SVN, Perforce, or Mercurial.
  - now: They can’t block the file change from occurring.
​ WorktreeCreate Runs when a worktree is being created, either from claude --worktree or from a subagent using isolation: "worktree" .
By default Claude Code creates the isolated working copy with git worktree .
Configuring a WorktreeCreate hook replaces that default git behavior, letting you use a different version control system like SVN, Perforce, or Mercurial.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The hook must return the absolute path to the created worktree directory.
  - now: The hook must return the path to the created worktree directory.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Command hooks print it on stdout; HTTP hooks return it via hookSpecificOutput.worktreePath .
  - now: See WorktreeCreate output for how each hook type returns the path.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This is a slug identifier for the new worktree, either specified by the user or auto-generated (for example, bold-oak-a3f2 ).
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "WorktreeCreate" , "name" : "feature-auth" } ​ WorktreeCreate output WorktreeCreate hooks do not use the standard allow/block decision model.
  - now: This is a slug identifier for the new worktree, either specified by the user or auto-generated, for example bold-oak-a3f2 .
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "WorktreeCreate" , "name" : "feature-auth" } ​ WorktreeCreate output WorktreeCreate hooks don’t use the standard allow/block decision model.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The hook must return the absolute path to the created worktree directory: Command hooks ( type: "command" ): print the path on stdout.
  - now: The hook must return the path to the created worktree directory: Command hooks ( type: "command" ): print the path as the last non-empty line of stdout.
Claude Code strips ANSI escape codes before reading that line, so shell startup banners printed before your echo are ignored.
Redirect any other hook output to stderr.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ WorktreeRemove The cleanup counterpart to WorktreeCreate .
This hook fires when a worktree is being removed, either when you exit a --worktree session and choose to remove it, or when a subagent with isolation: "worktree" finishes.
For git-based worktrees, Claude handles cleanup automatically with git worktree remove .
  - now: Claude Code resolves a relative path against the directory the hook ran in.
If the resulting path isn’t a directory Claude Code can enter, the session prints an error naming the path and exits with code 1.
Before v2.1.205, a relative path or a path that didn’t exist on disk crashed the session at startup, and with -p it stalled for about 30 seconds before exiting with code 0.
​ WorktreeRemove Runs when a worktree is being removed, either when you exit a --worktree session and choose to remove it, or when a subagent with isolation: "worktree" finishes.
This is the cleanup counterpart to WorktreeCreate .
For git-based worktrees, Claude Code handles cleanup automatically with git worktree remove .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block worktree removal but can perform cleanup tasks like removing version control state or archiving changes.
  - now: They can’t block worktree removal but can perform cleanup tasks like removing version control state or archiving changes.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot affect the compaction result but can perform follow-up tasks.
  - now: They can’t affect the compaction result but can perform follow-up tasks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block session termination but can perform cleanup tasks.
  - now: They can’t block session termination but can perform cleanup tasks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Timeouts set on plugin-provided hooks do not raise the budget.
  - now: Timeouts set on plugin-provided hooks don’t raise the budget.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For form-mode elicitation (the most common case): { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please provide your credentials" , "mode" : "form" , "requested_schema" : { "type" : "object" , "properties" : { "username" : { "type" : "string" , "title" : "Username" } } } } For URL-mode elicitation (browser-based authentication): { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please authenticate" , "mode" : "url" , "url" : "https://auth.example.com/login" } ​ Elicitation output To respond programmatically without showing the dialog, return a JSON object with hookSpecificOutput : { "hookSpecificOutput" : { "hookEventName" : "Elicitation" , "action" : "accept" , "content" : { "username" : "alice" } } } Field Values Description action accept , decline , cancel Whether to accept, decline, or cancel the request content object Form field values to submit.
  - now: For form-mode elicitation, the most common case: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please provide your credentials" , "mode" : "form" , "requested_schema" : { "type" : "object" , "properties" : { "username" : { "type" : "string" , "title" : "Username" } } } } For URL-mode elicitation, used for browser-based authentication: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please authenticate" , "mode" : "url" , "url" : "https://auth.example.com/login" } ​ Elicitation output To respond programmatically without showing the dialog, return a JSON object with hookSpecificOutput : { "hookSpecificOutput" : { "hookEventName" : "Elicitation" , "action" : "accept" , "content" : { "username" : "alice" } } } Field Values Description action accept , decline , cancel Whether to accept, decline, or cancel the request content object Form field values to submit.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They do not support http , prompt , or agent hooks.
  - now: They don’t support http , prompt , or agent hooks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The only output this event reads is hookSpecificOutput.retry , which prompt and agent hooks cannot set.
  - now: The only output this event reads is hookSpecificOutput.retry , which prompt and agent hooks can’t set.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Example: Multi-criteria Stop hook This Stop hook uses a detailed prompt to check three conditions before allowing Claude to stop.
If "ok" is false , Claude continues working with the provided reason as its next instruction.
SubagentStop hooks use the same format to evaluate whether a subagent should stop: { "hooks" : { "Stop" : [ { "hooks" : [ { "type" : "prompt" , "prompt" : "You are evaluating whether Claude should stop working.
  - now: ​ Check multiple conditions before stopping This Stop hook uses a detailed prompt to check three conditions before allowing Claude to stop.
SubagentStop hooks use the same format to evaluate whether a subagent should stop.
If "ok" is false , Claude continues working with the provided reason as its next instruction: { "hooks" : { "Stop" : [ { "hooks" : [ { "type" : "prompt" , "prompt" : "You are evaluating whether Claude should stop working.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Async hooks cannot block or control Claude’s behavior: response fields like decision , permissionDecision , and continue have no effect, because the action they would have controlled has already completed.
  - now: Async hooks can’t block or control Claude’s behavior: response fields like decision , permissionDecision , and continue have no effect, because the action they would have controlled has already completed.
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code validates that JSON response against the same output schema as synchronous hooks, and drops any field whose value has the wrong type, such as a systemMessage that isn’t a string, instead of delivering it.
Run with --debug to see a warning naming each dropped field.
Before v2.1.202, malformed JSON output from an async hook could crash the session, and the crash recurred each time the session was resumed.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Example: run tests after file changes This hook starts a test suite in the background whenever Claude writes a file, then reports the results back to Claude when the tests finish.
  - now: ​ Run tests after file changes This hook starts a test suite in the background whenever Claude writes a file, then reports the results back to Claude when the tests finish.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Prompt-based hooks cannot run asynchronously.
Async hooks cannot block tool calls or return decisions.
  - now: Prompt-based hooks can’t run asynchronously.
Async hooks can’t block tool calls or return decisions.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude Code auto-detects pwsh.exe (PowerShell 7+) with a fallback to powershell.exe (5.1).
{ "hooks" : { "PostToolUse" : [ { "matcher" : "Write" , "hooks" : [ { "type" : "command" , "shell" : "powershell" , "command" : "Write-Host 'File written'" } ] } ] } } To reference the project root from a PowerShell shell-form command, read it as an environment variable with $env:CLAUDE_PROJECT_DIR .
PowerShell treats the bare ${CLAUDE_PROJECT_DIR} form as a local variable, not an environment lookup, and Claude Code substitutes that placeholder in shell form only for plugin hooks .
For a hook defined in settings.json , either use the $env: form or switch to exec form , where ${CLAUDE_PROJECT_DIR} is substituted in each args element regardless of where the hook is defined.
The example below shows a settings.json hook that runs a project script with the $env: form: { "type" : "command" , "shell" : "powershell" , "command" : "& \" $env:CLAUDE_PROJECT_DIR \\ .claude \\ hooks \\ check.ps1 \" " } ​ Debug hooks Hook execution details, including which hooks matched, their exit codes, and full stdout and stderr, are written to the debug log file.
  - now: Claude Code auto-detects pwsh.exe , the PowerShell 7 and later executable, and falls back to powershell.exe for Windows PowerShell 5.1.
{ "hooks" : { "PostToolUse" : [ { "matcher" : "Write" , "hooks" : [ { "type" : "command" , "shell" : "powershell" , "command" : "Write-Host 'File written'" } ] } ] } } To reference the project root from a PowerShell shell-form command, write ${CLAUDE_PROJECT_DIR} or $env:CLAUDE_PROJECT_DIR .
As of v2.1.198, Claude Code rewrites the ${CLAUDE_PROJECT_DIR} , ${CLAUDE_PLUGIN_ROOT} , and ${CLAUDE_PLUGIN_DATA} placeholders in a PowerShell shell-form command to PowerShell’s ${env:NAME} form, whether the hook is defined in settings.json , a plugin, or a skill.
PowerShell then resolves the value from the exported environment after parsing, so the placeholder works inside double-quoted strings but not inside single-quoted strings, where PowerShell never expands variables.
Before v2.1.198, this rewrite applied only to plugin hooks.
On earlier versions, a settings.json hook needs the $env: form or exec form , where ${CLAUDE_PROJECT_DIR} is substituted in each args element regardless of where the hook is defined.
Don’t write the bare $CLAUDE_PROJECT_DIR spelling in a PowerShell hook.
PowerShell parses it as an undefined local variable and resolves it to $null , which leaves the script path without its project-root prefix.
Claude Code doesn’t rewrite that form; it logs a warning in the debug log instead.
The example below shows a settings.json hook that runs a project script with the $env: form, which works on every version: { "type" : "command" , "shell" : "powershell" , "command" : "& \" $env:CLAUDE_PROJECT_DIR \\ .claude \\ hooks \\ check.ps1 \" " } ​ Debug hooks Hook execution details, including which hooks matched, their exit codes, and full stdout and stderr, are written to the debug log file.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The --debug flag does not print to the terminal.
  - now: The --debug flag doesn’t print to the terminal.
