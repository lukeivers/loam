# Pending delta — claude-code-hooks

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://code.claude.com/docs/en/hooks`
> Projection target: `claude-code/hooks.md`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-15T13:10:31Z

- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Navigation Reference Hooks reference Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Hook lifecycle How a hook resolves Configuration Hook locations Matcher patterns Match MCP tools Hook handler fields Common fields Command hook fields HTTP hook fields MCP tool hook fields Prompt and agent hook fields Reference scripts by path Hooks in skills and agents The /hooks menu Disable or remove hooks Hook input and output Common input fields Exit code output Exit code 2 behavior per event HTTP response handling JSON output Emit terminal notifications Add context for Claude Decision control Hook events SessionStart SessionStart input SessionStart decision control Persist environment variables Setup Setup input Setup decision control InstructionsLoaded InstructionsLoaded input InstructionsLoaded decision control UserPromptSubmit UserPromptSubmit input UserPromptSubmit decision control UserPromptExpansion UserPromptExpansion input UserPromptExpansion decision control MessageDisplay MessageDisplay input MessageDisplay output PreToolUse PreToolUse input PreToolUse decision control Defer a tool call for later PermissionRequest PermissionRequest input PermissionRequest decision control Permission update entries PostToolUse PostToolUse input PostToolUse decision control PostToolUseFailure PostToolUseFailure input PostToolUseFailure decision control PostToolBatch PostToolBatch input PostToolBatch decision control PermissionDenied PermissionDenied input PermissionDenied decision control Notification Notification input SubagentStart SubagentStart input SubagentStop SubagentStop input TaskCreated TaskCreated input TaskCreated decision control TaskCompleted TaskCompleted input TaskCompleted decision control Stop Stop input Stop decision control StopFailure StopFailure input TeammateIdle TeammateIdle input TeammateIdle decision control ConfigChange ConfigChange input ConfigChange decision control CwdChanged CwdChanged input CwdChanged output FileChanged FileChanged input FileChanged output WorktreeCreate WorktreeCreate input WorktreeCreate output WorktreeRemove WorktreeRemove input PreCompact PreCompact input PostCompact PostCompact input SessionEnd SessionEnd input Elicitation Elicitation input Elicitation output ElicitationResult ElicitationResult input ElicitationResult output Prompt-based hooks How prompt-based hooks work Prompt hook configuration Response schema Example: Multi-criteria Stop hook Agent-based hooks How agent hooks work Agent hook configuration Run hooks in the background Configure an async hook How async hooks execute Example: run tests after file changes Limitations Security considerations Disclaimer Security best practices Windows PowerShell tool Debug hooks Reference Hooks reference Copy page Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, HTTP hooks, prompt hooks, and MCP tool hooks.
Copy page For a quickstart guide with examples, see Automate actions with hooks .
  - now: Navigation Reference Hooks reference Getting started Build with Claude Code Administration Configuration Reference Agent SDK What's New Resources Reference CLI reference Commands Environment variables Tools reference Interactive mode Checkpointing Hooks reference Plugins reference Channels reference Glossary Glossary On this page Hook lifecycle How a hook resolves Configuration Hook locations Matcher patterns Match MCP tools Hook handler fields Common fields Command hook fields HTTP hook fields MCP tool hook fields Prompt and agent hook fields Reference scripts by path Hooks in skills and agents The /hooks menu Disable or remove hooks Hook input and output Common input fields Exit code output Exit code 0 Exit code 2 Other exit codes Timeouts Exit code 2 behavior per event HTTP response handling JSON output Emit terminal notifications Add context for Claude Decision control Hook events SessionStart SessionStart input SessionStart decision control Persist environment variables Setup Setup input Setup decision control InstructionsLoaded InstructionsLoaded input InstructionsLoaded decision control UserPromptSubmit UserPromptSubmit input UserPromptSubmit decision control UserPromptExpansion UserPromptExpansion input UserPromptExpansion decision control MessageDisplay MessageDisplay input MessageDisplay output PreToolUse PreToolUse input PreToolUse decision control Defer a tool call for later PermissionRequest PermissionRequest input PermissionRequest decision control Permission update entries PostToolUse PostToolUse input PostToolUse decision control PostToolUseFailure PostToolUseFailure input PostToolUseFailure decision control PostToolBatch PostToolBatch input PostToolBatch decision control PermissionDenied PermissionDenied input PermissionDenied decision control Notification Notification input SubagentStart SubagentStart input SubagentStop SubagentStop input TaskCreated TaskCreated input TaskCreated decision control TaskCompleted TaskCompleted input TaskCompleted decision control Stop Stop input Stop decision control StopFailure StopFailure input TeammateIdle TeammateIdle input TeammateIdle decision control ConfigChange ConfigChange input ConfigChange decision control CwdChanged CwdChanged input CwdChanged output DirectoryAdded DirectoryAdded input FileChanged FileChanged input FileChanged output WorktreeCreate WorktreeCreate input WorktreeCreate output WorktreeRemove WorktreeRemove input PreCompact PreCompact input PostCompact PostCompact input SessionEnd SessionEnd input Elicitation Elicitation input Elicitation output ElicitationResult ElicitationResult input ElicitationResult output Prompt-based hooks How prompt-based hooks work Prompt hook configuration Response schema Check multiple conditions before stopping Agent-based hooks How agent hooks work Agent hook configuration Run hooks in the background Configure an async hook How async hooks execute Run tests after file changes Limitations Security considerations Disclaimer Workspace trust Security best practices Windows PowerShell tool Debug hooks Reference Hooks reference Copy page Copy page Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, HTTP hooks, prompt hooks, and MCP tool hooks.
Copy page Copy page For a quickstart guide with examples, see Automate actions with hooks .
- **new-claim** — adds a capability claim not previously upstream
  - now: Hooks run wherever Claude Code runs: sessions in the terminal, IDE extensions, the Desktop app , and Claude Code on the web all fire the same hook events.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: If you’re setting up hooks for the first time, start with the guide instead.
​ Hook lifecycle Hooks fire at specific points during a Claude Code session.
  - now: ​ Hook lifecycle Claude Code runs hooks at specific points during a session.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Events fall into three cadences: once per session ( SessionStart , SessionEnd ), once per turn ( UserPromptSubmit , Stop , StopFailure ), and on every tool call inside the agentic loop ( PreToolUse , PostToolUse ): The table below summarizes when each event fires.
  - now: Events fall into three cadences: once per session: SessionStart and SessionEnd once per turn: UserPromptSubmit , Stop , and StopFailure on every tool call inside the agentic loop: PreToolUse and PostToolUse , except EndConversation calls, which skip both The table below summarizes when each event fires.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Can block it PermissionRequest When a permission dialog appears PermissionDenied When a tool call is denied by the auto mode classifier.
Return {retry: true} to tell the model it may retry the denied tool call PostToolUse After a tool call succeeds PostToolUseFailure After a tool call fails PostToolBatch After a full batch of parallel tool calls resolves, before the next model call Notification When Claude Code sends a notification MessageDisplay While assistant message text is displayed SubagentStart When a subagent is spawned SubagentStop When a subagent finishes TaskCreated When a task is being created via TaskCreate TaskCompleted When a task is being marked as completed Stop When Claude finishes responding StopFailure When the turn ends due to an API error.
Output and exit code are ignored TeammateIdle When an agent team teammate is about to go idle InstructionsLoaded When a CLAUDE.md or .claude/rules/*.md file is loaded into context.
  - now: Can block it PermissionRequest When a tool call needs a permission decision PermissionDenied When auto mode denies a tool call, including denials without a classifier verdict.
Use JSON hookSpecificOutput.retry: true to tell the model it may retry the denied tool call.
Claude Code ignores retry when the classifier produced no verdict PostToolUse After a tool call succeeds PostToolUseFailure After a tool call fails PostToolBatch After a full batch of parallel tool calls resolves, before the next model call Notification When Claude Code sends a notification MessageDisplay While assistant message text is displayed SubagentStart When a subagent is spawned SubagentStop When a subagent finishes TaskCreated When a task is being created via TaskCreate TaskCompleted When a task is being marked as completed Stop When Claude finishes responding StopFailure When the turn ends due to an API error TeammateIdle When an agent team teammate is about to go idle InstructionsLoaded When a CLAUDE.md or .claude/rules/*.md file is loaded into context.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Useful for reactive environment management with tools like direnv FileChanged When a watched file changes on disk.
The matcher field specifies which filenames to watch WorktreeCreate When a worktree is being created via --worktree or isolation: "worktree" .
Replaces default git behavior WorktreeRemove When a worktree is being removed, either at session exit or when a subagent finishes PreCompact Before context compaction PostCompact After context compaction completes Elicitation When an MCP server requests user input during a tool call ElicitationResult After a user responds to an MCP elicitation, before the response is sent back to the server SessionEnd When a session terminates ​ How a hook resolves To see how these pieces fit together, consider this PreToolUse hook that blocks destructive shell commands.
The matcher narrows to Bash tool calls and the if condition narrows further to Bash subcommands matching rm * , so block-rm.sh only spawns when both filters match: { "hooks" : { "PreToolUse" : [ { "matcher" : "Bash" , "hooks" : [ { "type" : "command" , "if" : "Bash(rm *)" , "command" : "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh" , "args" : [] } ] } ] } } The script reads the JSON input from stdin, extracts the command, and returns a permissionDecision of "deny" if it contains rm -rf : #!/bin/bash # .claude/hooks/block-rm.sh COMMAND = $( jq -r '.tool_input.command' ) if echo " $COMMAND " | grep -q 'rm -rf' ; then jq -n '{ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: "Destructive command blocked by hook" } }' else exit 0 # no decision; normal permission flow applies fi Now suppose Claude Code decides to run Bash "rm -rf /tmp/build" .
  - now: Useful for reactive environment management with tools like direnv DirectoryAdded When a working directory is added mid-session via /add-dir or the SDK register_repo_root control request FileChanged When a watched file changes on disk.
The matcher field specifies which filenames to watch WorktreeCreate When a worktree is being created via --worktree , isolation: "worktree" , or for a background session.
Replaces default git behavior WorktreeRemove When a worktree is being removed at session exit, when a subagent finishes, or when you delete a background session PreCompact Before context compaction PostCompact After context compaction completes Elicitation When an MCP server requests user input during a tool call ElicitationResult After a user responds to an MCP elicitation, before the response is sent back to the server SessionEnd When a session terminates ​ How a hook resolves To see how these pieces fit together, consider this PreToolUse hook that blocks destructive shell commands.
macOS/Linux Windows (PowerShell) The matcher narrows to Bash tool calls and the if condition narrows further to Bash subcommands matching rm * , so block-rm.sh only spawns when both filters match: { "hooks" : { "PreToolUse" : [ { "matcher" : "Bash" , "hooks" : [ { "type" : "command" , "if" : "Bash(rm *)" , "command" : "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh" , "args" : [] } ] } ] } } The script reads the JSON input from stdin, extracts the command, and returns a permissionDecision of "deny" if it contains rm -rf .
Save it to .claude/hooks/block-rm.sh in your project and make it executable with chmod +x .claude/hooks/block-rm.sh so Claude Code can run it: #!/bin/bash # .claude/hooks/block-rm.sh COMMAND = $( jq -r '.tool_input.command' ) if echo " $COMMAND " | grep -q 'rm -rf' ; then jq -n '{ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: "Destructive command blocked by hook" } }' else exit 0 # no decision; normal permission flow applies fi This script, like the other Bash examples on this page that parse JSON input, uses jq , so install jq and make sure it is on your PATH before trying them.
The matcher Bash|PowerShell covers the PowerShell tool as well as Bash.
A single if rule matches only one tool’s calls, so each tool gets its own handler: the first narrows to Bash subcommands matching rm * , the second to PowerShell commands matching Remove-Item * .
Both run the same script through powershell.exe : { "hooks" : { "PreToolUse" : [ { "matcher" : "Bash|PowerShell" , "hooks" : [ { "type" : "command" , "if" : "Bash(rm *)" , "command" : "powershell.exe" , "args" : [ "-NoProfile" , "-ExecutionPolicy" , "Bypass" , "-File" , "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.ps1" ] }, { "type" : "command" , "if" : "PowerShell(Remove-Item *)" , "command" : "powershell.exe" , "args" : [ "-NoProfile" , "-ExecutionPolicy" , "Bypass" , "-File" , "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.ps1" ] } ] } ] } } The -NoProfile flag skips loading your PowerShell profile so the hook starts fast, and -ExecutionPolicy Bypass lets PowerShell run the local script file.
The script reads the JSON input from stdin, extracts the command, and returns a permissionDecision of "deny" if it contains rm -rf or Remove-Item followed by -Recurse .
Save it to .claude/hooks/block-rm.ps1 in your project: # .claude/hooks/block-rm.ps1 $callInput = [ Console ]:: In .ReadToEnd() | ConvertFrom-Json $command = $callInput .tool_input.command if ( $command -match 'rm -rf|Remove-Item.*-Recurse' ) { @ { hookSpecificOutput = @ { hookEventName = "PreToolUse" permissionDecision = "deny" permissionDecisionReason = "Destructive command blocked by hook" } } | ConvertTo-Json } else { exit 0 # no decision; normal permission flow applies } Now suppose Claude Code decides to run Bash "rm -rf /tmp/build" against the macOS/Linux config.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Hook locations Where you define a hook determines its scope: Location Scope Shareable ~/.claude/settings.json All your projects No, local to your machine .claude/settings.json Single project Yes, can be committed to the repo .claude/settings.local.json Single project No, gitignored when Claude Code creates it Managed policy settings Organization-wide Yes, admin-controlled Plugin hooks/hooks.json When plugin is enabled Yes, bundled with the plugin Skill or agent frontmatter While the component is active Yes, defined in the component file For details on settings file resolution, see settings .
Enterprise administrators can use allowManagedHooksOnly to block user, project, and plugin hooks.
Hooks from plugins force-enabled in managed settings enabledPlugins are exempt, so administrators can distribute vetted hooks through an organization marketplace.
See Hook configuration .
​ Matcher patterns The matcher field filters when hooks fire.
  - now: ​ Hook locations Where you define a hook determines its scope: Location Scope Shareable ~/.claude/settings.json All your projects No, local to your machine .claude/settings.json Single project Yes, can be committed to the repo .claude/settings.local.json Single project No, gitignored when Claude Code saves a setting to it Managed policy settings Organization-wide Yes, admin-controlled Plugin hooks/hooks.json When plugin is enabled Yes, bundled with the plugin Skill frontmatter The rest of the session once the skill is invoked.
See Hooks in skills and agents Yes, defined in the skill file Subagent frontmatter While that subagent is running Yes, defined in the subagent file Cloud sessions on Claude Code on the web don’t read your local ~/.claude/settings.json ; hooks there come from the repo and from your organization’s server-managed settings.
See what carries over from your setup for which files reach a cloud session.
For details on settings file resolution, see settings .
Hooks from settings files, managed policy settings, and plugins also run inside subagents .
When a subagent calls a tool, tool events such as PreToolUse and PostToolUse fire the same configured hooks as in the main conversation, and the input carries the agent_id and agent_type common input fields that identify the subagent.
Enterprise administrators can use allowManagedHooksOnly to restrict which hooks run: Your user, project, local, and plugin hooks are blocked.
Hooks from plugins force-enabled in managed settings enabledPlugins are exempt Claude Code also narrows your statusLine , fileSuggestion , and subagentStatusLine settings to managed settings Claude Code also disables plugins with a command source , including plugins force-enabled in managed settings enabledPlugins , unless disableCommandPluginSources is explicitly set to false See Hook configuration .
Hook entries merge across settings levels rather than replacing each other: user, project, and local settings add their own hooks without removing managed ones, and the disableAllHooks setting can’t disable managed hooks from outside managed settings.
The HTTP hook allowlists apply to hooks from every source, including managed policy settings: allowedHttpHookUrls : when defined at any settings level, Claude Code runs an HTTP hook handler only if its URL matches the merged allowlist httpHookAllowedEnvVars : when defined, Claude Code interpolates only the environment variables on that list into hook headers ​ Matcher patterns The matcher field filters when hooks fire.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The FileChanged event does not follow these rules when building its watch list.
  - now: The FileChanged event doesn’t follow these rules when building its watch list.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Each event type matches on a different field: Event What the matcher filters Example matcher values PreToolUse , PostToolUse , PostToolUseFailure , PermissionRequest , PermissionDenied tool name Bash , Edit|Write , mcp__.* SessionStart how the session started startup , resume , clear , compact Setup which CLI flag triggered setup init , maintenance SessionEnd why the session ended clear , resume , logout , prompt_input_exit , bypass_permissions_disabled , other Notification notification type permission_prompt , idle_prompt , auth_success , elicitation_dialog , elicitation_complete , elicitation_response SubagentStart agent type general-purpose , Explore , Plan , custom agent names, or plugin-scoped names like ^my-plugin:reviewer$ PreCompact , PostCompact what triggered compaction manual , auto SubagentStop agent type same values as SubagentStart ConfigChange configuration source user_settings , project_settings , local_settings , policy_settings , skills CwdChanged no matcher support always fires on every directory change FileChanged literal filenames to watch (see FileChanged ) .envrc|.env StopFailure error type rate_limit , overloaded , authentication_failed , oauth_org_not_allowed , billing_error , invalid_request , model_not_found , server_error , max_output_tokens , unknown InstructionsLoaded load reason session_start , nested_traversal , path_glob_match , include , compact UserPromptExpansion command name your skill or command names Elicitation MCP server name your configured MCP server names ElicitationResult MCP server name same values as Elicitation UserPromptSubmit , PostToolBatch , Stop , TeammateIdle , TaskCreated , TaskCompleted , WorktreeCreate , WorktreeRemove , MessageDisplay no matcher support always fires on every occurrence The matcher runs against a field from the JSON input that Claude Code sends to your hook on stdin.
  - now: Each event type matches on a different field: Event What the matcher filters Example matcher values PreToolUse , PostToolUse , PostToolUseFailure , PermissionRequest , PermissionDenied tool name Bash , Edit|Write , mcp__.* SessionStart how the session started startup , resume , clear , compact , fork Setup which CLI flag triggered setup init , maintenance SessionEnd why the session ended clear , resume , logout , prompt_input_exit , bypass_permissions_disabled , other Notification notification type permission_prompt , idle_prompt , auth_success , elicitation_dialog , elicitation_url_dialog , elicitation_complete , elicitation_response , agent_needs_input , agent_completed SubagentStart agent type general-purpose , Explore , Plan , custom agent names, or plugin-scoped names like ^my-plugin:reviewer$ PreCompact , PostCompact what triggered compaction manual , auto SubagentStop agent type same values as SubagentStart ConfigChange configuration source user_settings , project_settings , local_settings , policy_settings , skills CwdChanged no matcher support always fires on every directory change DirectoryAdded how the directory was added slash_command , register_repo_root FileChanged literal filenames to watch (see FileChanged ) .envrc|.env StopFailure error type rate_limit , overloaded , authentication_failed , oauth_org_not_allowed , billing_error , invalid_request , model_not_found , server_error , max_output_tokens , unknown InstructionsLoaded load reason session_start , nested_traversal , path_glob_match , include , compact UserPromptExpansion command name your skill or command names Elicitation MCP server name your configured MCP server names ElicitationResult MCP server name same values as Elicitation UserPromptSubmit , PostToolBatch , Stop , TeammateIdle , TaskCreated , TaskCompleted , WorktreeCreate , WorktreeRemove , MessageDisplay no matcher support always fires on every occurrence The matcher runs against a field from the JSON input that Claude Code sends to your hook on stdin.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This example runs a linting script only when Claude writes or edits a file: { "hooks" : { "PostToolUse" : [ { "matcher" : "Edit|Write" , "hooks" : [ { "type" : "command" , "command" : "/path/to/lint-check.sh" } ] } ] } } UserPromptSubmit , PostToolBatch , Stop , TeammateIdle , TaskCreated , TaskCompleted , WorktreeCreate , WorktreeRemove , MessageDisplay , and CwdChanged don’t support matchers and always fire on every occurrence.
If you add a matcher field to these events, it is silently ignored.
  - now: This example runs a linting script only when Claude writes or edits a file: { "hooks" : { "PostToolUse" : [ { "matcher" : "Edit|Write" , "hooks" : [ { "type" : "command" , "command" : "/path/to/lint-check.sh" } ] } ] } } If you add a matcher field to an event without matcher support, it is silently ignored.
- **new-claim** — adds a capability claim not previously upstream
  - now: Tools from a plugin-bundled MCP server use a scoped server segment that includes the plugin name: mcp__plugin_<plugin-name>_<server-name>__<tool> .
A matcher written against the bare server key never fires for these tools.
For a plugin named my-plugin that bundles a server under the key db , a query tool appears as mcp__plugin_my-plugin_db__query , so the matcher for every tool from that server is mcp__plugin_my-plugin_db__.* .
Use the same scoped tool name in a handler’s if field .
See Plugin-provided MCP servers for how the scoped name is built.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The model returns a yes/no decision as JSON.
  - now: The model returns its decision as JSON.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: All matching hooks run in parallel, and identical handlers are deduplicated automatically.
Command hooks are deduplicated by command string and args , and HTTP hooks are deduplicated by URL.
  - now: All matching hooks run in parallel.
If you define the same handler in more than one settings file, it runs once.
A plugin’s or skill’s copy of the same handler stays separate.
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.199, $CLAUDE_CODE_BRIDGE_SESSION_ID is set to the Remote Control session ID while the local session has an active Remote Control connection.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: UserPromptSubmit lowers the command , http , and mcp_tool default to 30, and MessageDisplay lowers it to 10 statusMessage no Custom spinner message displayed while the hook runs once no If true , runs once per session then is removed.
  - now: UserPromptSubmit lowers the command , http , and mcp_tool default to 30, and MessageDisplay lowers it to 10.
SessionEnd hooks share a 1.5-second budget; if your settings set a longer per-hook timeout , Claude Code raises the budget to match, up to 60 seconds statusMessage no Custom spinner message displayed while the hook runs once no If true , runs once per session then is removed.
- **new-claim** — adds a capability claim not previously upstream
  - now: In an if condition for a file tool, a single-segment directory pattern like "Edit(src/**)" matches only the src directory in the working directory and the files under it.
To match a directory named src at any depth, write "Edit(**/src/**)" .
Before v2.1.214, "Edit(src/**)" matched a directory named src at any depth under the working directory.
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
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Error handling differs from command hooks: non-2xx responses, connection failures, and timeouts all produce non-blocking errors that allow execution to continue.
To block a tool call or deny a permission, return a 2xx response with a JSON body containing decision: "block" or a hookSpecificOutput with permissionDecision: "deny" .
  - now: Error handling differs from command hooks; see HTTP response handling .
- **new-claim** — adds a capability claim not previously upstream
  - now: For a plugin-bundled server , this is the scoped name plugin:<plugin-name>:<server-name> , such as plugin:my-plugin:db , not the bare server key.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: String values support ${path} substitution from the hook’s JSON input , such as "${tool_input.file_path}" The tool’s text content is treated like command-hook stdout: if it parses as valid JSON output it is processed as a decision, otherwise it is shown as plain text.
  - now: String values support ${path} substitution from the hook’s JSON input , such as "${tool_input.file_path}" Claude Code reads the tool’s text content the same way it reads command-hook stdout, following the parsing rule under exit code 0 .
- **removal** — removes a previously-present capability claim
  - was: Exec form passes each args element as one argument with no shell tokenization, so paths with spaces or special characters need no quoting.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Hooks in skills and agents In addition to settings files and plugins, hooks can be defined directly in skills and subagents using frontmatter.
These hooks are scoped to the component’s lifecycle and only run when that component is active.
  - now: ​ Hooks in skills and agents In addition to settings files and plugins, hooks can be defined directly in skills and subagents using frontmatter, in the same configuration format as settings-based hooks.
How long Claude Code keeps them registered depends on the component: Subagent hooks : Claude Code runs them only while that subagent is running and removes them when it finishes.
Claude Code converts a Stop hook here to SubagentStop , the event it fires when a subagent completes.
Skill hooks : Claude Code registers them when you or Claude invoke the skill and keeps running them for the rest of the session, on turns after the skill’s own turn as well.
To have Claude Code run a hook a single time instead, set once: true on it.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: For subagents, Stop hooks are automatically converted to SubagentStop since that is the event that fires when a subagent completes.
Hooks use the same configuration format as settings-based hooks but are scoped to the component’s lifetime and cleaned up when it finishes.
This skill defines a PreToolUse hook that runs a security validation script before each Bash command: --- name : secure-operations description : Perform operations with security checks hooks : PreToolUse : - matcher : "Bash" hooks : - type : command command : "./scripts/security-check.sh" --- Agents use the same format in their YAML frontmatter.
  - now: This skill defines a PreToolUse hook that runs a security validation script before each Bash command: --- name : secure-operations description : Perform operations with security checks hooks : PreToolUse : - matcher : "Bash" hooks : - type : command command : "./scripts/security-check.sh" --- Subagents use the same format in their YAML frontmatter.
Frontmatter hooks in a project skill follow the same workspace trust rule as hooks in settings files .
Claude Code registers them when you or Claude invoke the skill, including in a -p run in a folder you haven’t trusted.
Frontmatter hooks in a project subagent run only after you accept the workspace trust dialog for the folder the agent file came from.
A -p session doesn’t count as accepting it.
What runs before you trust a folder compares this with the settings-file rule, and the subagents page lists which scopes are exempt .
Before v2.1.218, these hooks could run from folders you hadn’t trusted.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Each hook is labeled with a [type] prefix and a source indicating where it was defined: User : from ~/.claude/settings.json Project : from .claude/settings.json Local : from .claude/settings.local.json Plugin : from a plugin’s hooks/hooks.json Session : registered in memory for the current session Built-in : registered internally by Claude Code Selecting a hook opens a detail view showing its event, matcher, type, source file, and the full command, prompt, or URL.
  - now: Each hook is labeled with a [type] prefix and a source indicating where it was defined: User Settings : from ~/.claude/settings.json Project Settings : from .claude/settings.json Local Settings : from .claude/settings.local.json Plugin Hooks : from a plugin’s hooks/hooks.json Session Hooks : registered in memory for the current session Built-in Hooks : registered internally by Claude Code Selecting a hook opens a detail view showing its event, matcher, type, source file, and the full command, prompt, or URL.
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code reads the value left after settings precedence applies, so a "disableAllHooks": false in a project’s .claude/settings.json overrides a true in your user settings.
To turn hooks off for one run whatever the project’s settings say, pass --settings '{"disableAllHooks": true}' , which takes precedence over project and local settings.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: If an administrator has configured hooks through managed policy settings, disableAllHooks set in user, project, or local settings cannot disable those managed hooks.
  - now: If an administrator has configured hooks through managed policy settings, disableAllHooks set in user, project, or local settings can’t disable those managed hooks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: On macOS and Linux, command hooks run in their own session without a controlling terminal as of v2.1.139.
The hook process and any child processes cannot open /dev/tty or send escape sequences directly to the Claude Code interface.
  - now: On macOS and Linux, command hooks run in their own session without a controlling terminal.
The hook process and any child processes can’t open /dev/tty or send escape sequences directly to the Claude Code interface.
- **new-claim** — adds a capability claim not previously upstream
  - now: Some events discard it or deliver it elsewhere, and each event’s section says so.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Requires Claude Code v2.1.196 or later transcript_path Path to conversation JSON cwd Current working directory when the hook is invoked permission_mode Current permission mode : "default" , "plan" , "acceptEdits" , "auto" , "dontAsk" , or "bypassPermissions" .
Not all events receive this field: see each event’s JSON example below to check effort Object with a level field holding the active effort level for the turn: "low" , "medium" , "high" , "xhigh" , or "max" .
  - now: Requires Claude Code v2.1.196 or later transcript_path Path to conversation JSON.
The transcript file is written asynchronously and may lag the in-memory conversation, so it may not yet include the current turn’s most recent messages when a hook fires.
Hooks that need the final assistant text of the current turn should use last_assistant_message on Stop and SubagentStop instead of reading the transcript cwd Current working directory when the hook is invoked permission_mode Current permission mode : "default" , "plan" , "acceptEdits" , "auto" , "dontAsk" , or "bypassPermissions" .
The mode labeled Manual arrives as "default" , never as "manual" , so scripts that match "default" keep working.
Not all events receive this field.
Check the JSON example in each hook event section effort Object with a level field holding the active effort level for the turn: "low" , "medium" , "high" , "xhigh" , or "max" .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: For custom subagents , this is the name field from the agent’s frontmatter, not the filename.
For subagents shipped by a plugin , this is the plugin-scoped identifier such as my-plugin:reviewer , not the bare frontmatter name.
See SubagentStart for how to write a matcher against a plugin-scoped name.
  - now: See SubagentStart for the values custom and plugin subagents report and how to write a matcher against a plugin-scoped name.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: A hook process inherits the parent environment, so it can read $ANTHROPIC_MODEL if you set it in your shell, but that value does not change when you switch models with /model during a session.
For example, a PreToolUse hook for a Bash command receives this on stdin: { "session_id" : "abc123" , "prompt_id" : "550e8400-e29b-41d4-a716-446655440000" , "transcript_path" : "/home/user/.claude/projects/.../transcript.jsonl" , "cwd" : "/home/user/my-project" , "permission_mode" : "default" , "hook_event_name" : "PreToolUse" , "tool_name" : "Bash" , "tool_input" : { "command" : "npm test" } } The tool_name and tool_input fields are event-specific.
  - now: A hook process inherits the parent environment, so it can read $ANTHROPIC_MODEL if you set it in your shell, but that value doesn’t change when you switch models with /model during a session.
One set of variables is not inherited: Claude Code removes OTEL_* exporter variables from every subprocess it spawns , including hooks.
For example, a PreToolUse hook for a Bash command receives this on stdin: { "session_id" : "abc123" , "prompt_id" : "550e8400-e29b-41d4-a716-446655440000" , "transcript_path" : "/home/user/.claude/projects/.../transcript.jsonl" , "cwd" : "/home/user/my-project" , "permission_mode" : "default" , "hook_event_name" : "PreToolUse" , "tool_name" : "Bash" , "tool_input" : { "command" : "npm test" , "description" : "Run test suite" , "timeout" : 120000 , "run_in_background" : false }, "tool_use_id" : "toolu_01ABC123..." } The tool_name , tool_input , and tool_use_id fields are event-specific.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Exit 0 means success.
Claude Code parses stdout for JSON output fields .
JSON output is only processed on exit 0.
  - now: The exit code doesn’t act alone.
Claude Code reads JSON output fields from stdout on every exit code, not just 0, and for events that use the standard decision model, a parsed object that passes schema validation takes effect alongside the code.
Exit 2’s block is the one outcome JSON can’t override.
Two tables own the per-event exceptions: Exit code 2 behavior per event says what exit codes do for each event, and Decision control says which decision fields each event honors.
Universal fields such as systemMessage work across most events and are listed in the JSON output table.
​ Exit code 0 Exit 0 means success, and is the intended exit code when you print JSON for structured control.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The exceptions are UserPromptSubmit , UserPromptExpansion , and SessionStart , where stdout is added as context that Claude can see and act on.
Exit 2 means a blocking error.
Claude Code ignores stdout and any JSON in it.
Instead, stderr text is fed back to Claude as an error message.
The effect depends on the event: PreToolUse blocks the tool call, UserPromptSubmit rejects the prompt, and so on.
See exit code 2 behavior for the full list.
Any other exit code is a non-blocking error for most hook events.
The transcript shows a <hook name> hook error notice followed by the first line of stderr, so you can identify the cause without --debug .
Execution continues and the full stderr is written to the debug log.
For example, a hook command script that blocks dangerous Bash commands: #!/bin/bash # Reads JSON input from stdin, checks the command command = $( jq -r '.tool_input.command' < /dev/stdin ) if [[ " $command " == rm * ]]; then echo "Blocked: rm commands are not allowed" >&2 exit 2 # Blocking error: tool call is prevented fi exit 0 # No decision: the normal permission flow applies For most hook events, only exit code 2 blocks the action.
Claude Code treats exit code 1 as a non-blocking error and proceeds with the action, even though 1 is the conventional Unix failure code.
  - now: The exceptions are UserPromptSubmit , UserPromptExpansion , and SessionStart , where Claude Code adds plain-text stdout as context that Claude can see and act on.
Whether Claude Code reads your stdout as JSON output or as plain text depends on its first character, ignoring leading whitespace: Starts with { : Claude Code parses it as JSON.
If it isn’t valid JSON, Claude Code treats it as plain text.
Starts with anything else : Claude Code treats it as plain text, a JSON array or a quoted JSON string included.
For events that use the standard decision model, exit 0 with a parsed object that fails schema validation is a non-blocking error: the action proceeds, and the transcript shows a <hook name> hook error notice with the validation message.
The same happens on any exit code other than 2, while exit 2 still blocks .
Stderr from a hook that exits 0 goes to the debug log only, never the transcript, and Claude never sees it.
To read it yourself, enable debug logging .
To surface a warning to Claude from a PostToolUse or PostToolUseFailure hook, exit 2 instead so Claude sees the stderr even though the tool already ran.
​ Exit code 2 Exit 2 means a blocking error.
On events that can block , exit 2 blocks whether or not you print JSON: even a JSON permissionDecision of "allow" can’t override it.
Claude Code still reads any valid JSON output on stdout.
On Elicitation and ElicitationResult , an exit-2 hook’s hookSpecificOutput is ignored.
The blocking message is the reason from your JSON’s blocking decision when it makes one, and your stderr text otherwise.
What the block does varies by event: PreToolUse blocks the tool call, UserPromptSubmit rejects the prompt, and so on.
Exit code 2 behavior per event lists the effect for every event, and each event’s section says where the message goes.
A hook that exits 2 while printing JSON that fails JSON output schema validation still blocks: Claude Code uses stderr as the blocking reason and records the validation failure in the debug log.
Before v2.1.214, Claude Code treated that combination as a non-blocking error and the action proceeded.
This script blocks rm commands by exiting 2 and leaves every other command to the normal permission flow: #!/bin/bash # Reads JSON input from stdin, checks the command input = $( cat ) command = $( jq -r '.tool_input.command' <<< " $input " ) if [[ " $command " == rm * ]]; then echo "Blocked: rm commands are not allowed" >&2 exit 2 # Blocking error: tool call is prevented fi exit 0 # No decision: the normal permission flow applies ​ Other exit codes Any other exit code doesn’t block on its own for most hook events.
What happens depends on your stdout: With a parsed object that passes schema validation, for events that use the standard decision model, Claude Code ignores the exit code and the JSON alone decides the outcome: Each field the event supports is honored, including permissionDecision , additionalContext , updatedInput , and systemMessage , and the hook isn’t reported as an error.
Decision control lists the decision fields per event; universal fields like systemMessage follow the JSON output table.
With a parsed object that fails schema validation, for events that use the standard decision model, it’s the same non-blocking error as on exit 0 : the action proceeds, and the <hook name> hook error notice carries the validation message.
With stdout that Claude Code treats as plain text , or with empty stdout, it’s a non-blocking error for most hook events: the action proceeds, and the transcript shows a <hook name> hook error notice followed by the first line of stderr, prefixed with Failed with non-blocking status code: .
To capture the full stderr, enable debug logging .
Events outside the standard decision model keep their own rows in the per-event table : WorktreeCreate fails creation on any nonzero exit no matter what your JSON says, and events that discard hook output entirely, like StopFailure , ignore your JSON on every exit code, apart from side-effect fields like terminalSequence , which still fire.
A hook that can’t start lands in the same non-blocking bucket.
When the script path doesn’t exist or isn’t executable, the shell exits with a code like 127 and you see the same notice with the interpreter’s message, for example Failed with non-blocking status code: /bin/sh: /path/to/hook.sh: No such file or directory .
For most hook events, the action proceeds.
When you set up a policy hook, watch for this notice on its first run: a mistyped path in settings.json leaves the gate silently disabled.
For most hook events, exit code 2 is the only exit code that blocks through the code alone.
Without valid JSON on stdout, Claude Code treats exit code 1 as a non-blocking error and proceeds with the action, even though 1 is the conventional Unix failure code.
- **new-claim** — adds a capability claim not previously upstream
  - now: ​ Timeouts A command , http , or mcp_tool hook that reaches its timeout is canceled: Claude Code discards the hook’s output, and the hook renders no decision.
On PreToolUse , the two hook families differ: A timed-out command , http , or mcp_tool hook doesn’t block the tool call.
The call continues through the normal permission flow , so don’t count on a stalled hook to act as a gate.
An Agent SDK callback hook that exceeds its timeout blocks the tool call .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: What happens on exit 2 PreToolUse Yes Blocks the tool call PermissionRequest Yes Denies the permission UserPromptSubmit Yes Blocks prompt processing and erases the prompt UserPromptExpansion Yes Blocks the expansion Stop Yes Prevents Claude from stopping, continues the conversation SubagentStop Yes Prevents the subagent from stopping TeammateIdle Yes Prevents the teammate from going idle (teammate continues working) TaskCreated Yes Rolls back the task creation TaskCompleted Yes Prevents the task from being marked as completed ConfigChange Yes Blocks the configuration change from taking effect (except policy_settings ) StopFailure No Output and exit code are ignored PostToolUse No Shows stderr to Claude (tool already ran) PostToolUseFailure No Shows stderr to Claude (tool already failed) PostToolBatch Yes Stops the agentic loop before the next model call PermissionDenied No Exit code and stderr are ignored (denial already occurred).
Use JSON hookSpecificOutput.retry: true to tell the model it may retry Notification No Shows stderr to user only SubagentStart No Shows stderr to user only SessionStart No Shows stderr to user only Setup No Shows stderr to user only SessionEnd No Shows stderr to user only CwdChanged No Shows stderr to user only FileChanged No Shows stderr to user only PreCompact Yes Blocks compaction PostCompact No Shows stderr to user only Elicitation Yes Denies the elicitation ElicitationResult Yes Blocks the response (action becomes decline) WorktreeCreate Yes Any non-zero exit code causes worktree creation to fail WorktreeRemove No Failures are logged in debug mode only InstructionsLoaded No Exit code is ignored MessageDisplay No The original text is displayed ​ HTTP response handling HTTP hooks use HTTP status codes and response bodies instead of exit codes and stdout: 2xx with an empty body : success, equivalent to exit code 0 with no output 2xx with a plain text body : success, the text is added as context 2xx with a JSON body : success, parsed using the same JSON output schema as command hooks Non-2xx status : non-blocking error, execution continues Connection failure or timeout : non-blocking error, execution continues Unlike command hooks, HTTP hooks cannot signal a blocking error through status codes alone.
  - now: What happens on exit 2 PreToolUse Yes Blocks the tool call PermissionRequest No Exit code 2 isn’t honored for this event and the permission flow proceeds unchanged.
Deny through the decision object instead UserPromptSubmit Yes Blocks prompt processing and erases the prompt UserPromptExpansion Yes Blocks the expansion Stop Yes Prevents Claude from stopping, continues the conversation SubagentStop Yes Prevents the subagent from stopping TeammateIdle Yes Prevents the teammate from going idle, so it continues working TaskCreated Yes Rolls back the task creation TaskCompleted Yes Prevents the task from being marked as completed ConfigChange Yes Blocks the configuration change from taking effect (except policy_settings ) StopFailure No Output and exit code are ignored, except terminalSequence PostToolUse No Shows stderr to Claude; the tool already ran PostToolUseFailure No Shows stderr to Claude; the tool already failed PostToolBatch Yes Stops the agentic loop before the next model call PermissionDenied No Exit code and stderr are ignored because the denial already occurred.
Use JSON hookSpecificOutput.retry: true to tell the model it may retry; Claude Code ignores retry: true for no-verdict denials Notification No Exit code and stderr are ignored SubagentStart No Shows stderr to user only SessionStart No Shows stderr to user only Setup No Shows stderr to user only SessionEnd No Shows stderr to user only CwdChanged No Shows stderr to user only DirectoryAdded No Stderr goes to the debug log; the directory is already added FileChanged No Shows stderr to user only PreCompact Yes Blocks compaction PostCompact No Shows stderr to user only Elicitation Yes Denies the elicitation ElicitationResult Yes Blocks the response (action becomes decline) WorktreeCreate Yes Any non-zero exit code causes worktree creation to fail WorktreeRemove No Failures are logged in debug mode only InstructionsLoaded No Exit code is ignored MessageDisplay No The original text is displayed For SessionStart , Setup , and SubagentStart , the exit code 2 stderr renders in the transcript as a <hook name> hook error notice, the same way a non-blocking error does.
Claude doesn’t see it, and the session or subagent proceeds.
For SubagentStart , the notice appears in the subagent’s own transcript, not in the parent conversation.
​ HTTP response handling HTTP hooks use HTTP status codes and response bodies instead of exit codes and stdout.
The outcomes below apply to most events; an event with its own failure contract in the per-event table , such as WorktreeCreate , applies that contract to a failed HTTP hook too: 2xx with an empty body : success, equivalent to exit code 0 with no output 2xx with a JSON object body : parsed using the same JSON output schema as command hooks.
A body that fails schema validation is a non-blocking error 2xx with any other body, such as plain text : non-blocking error, handled the same as a non-2xx status.
Claude Code doesn’t add the text to Claude’s context Non-2xx status : non-blocking error, execution continues Connection failure : non-blocking error, execution continues Timeout : the hook is canceled and renders no decision, and execution continues Unlike command hooks, HTTP hooks can’t signal a blocking error through status codes alone.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: You must choose one approach per hook, not both: either use exit codes alone for signaling, or exit 0 and print JSON for structured control.
Claude Code only processes JSON on exit 0.
If you exit 2, any JSON is ignored.
  - now: Choose one approach per hook: either use exit codes alone for signaling, or exit 0 and print JSON for structured control.
If you mix them, exit 2 keeps its blocking effect , and Claude Code still reads the JSON fields, with the one elicitation exception noted under Exit code 2 .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: See JSON validation failed in the troubleshooting guide.
  - now: See Hook JSON has no effect in the troubleshooting guide.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Output that exceeds this limit is saved to a file and replaced with a preview and file path, the same way large tool results are handled.
The JSON object supports three kinds of fields: Universal fields like continue work across all events.
These are listed in the table below.
  - now: Output that exceeds this limit is saved to a file and replaced with a preview and file path, the same way a large valid Bash result is handled under Output limits .
The JSON object supports three kinds of fields: Universal fields like continue are listed in the table below.
Every event accepts them, but some events discard them or deliver systemMessage somewhere other than the transcript.
Each event’s section says so.
terminalSequence works on those events too, with the exceptions listed under Emit terminal notifications .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Not shown to Claude suppressOutput false If true , hides the hook’s stdout from the transcript.
Stdout still appears in the debug log systemMessage none Warning message shown to the user terminalSequence none A terminal escape sequence for Claude Code to emit on your behalf, such as a desktop notification, window title, or bell.
  - now: Not shown to Claude suppressOutput false Has no effect: Claude Code accepts the field but doesn’t act on it.
A successful hook’s stdout is never shown in the transcript and is recorded in the debug log systemMessage none Warning message shown to the user.
In Agent SDK and --output-format stream-json output, it can arrive as an SDKInformationalMessage terminalSequence none A terminal escape sequence for Claude Code to emit on your behalf, such as a desktop notification, window title, or bell.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Use this instead of writing to /dev/tty , which is unavailable to hooks To stop Claude entirely regardless of event type: { "continue" : false , "stopReason" : "Build failed, fix errors before continuing" } ​ Emit terminal notifications The terminalSequence field requires Claude Code v2.1.141 or later.
Hooks run without a controlling terminal, so writing escape sequences directly to /dev/tty fails.
  - now: Use this instead of writing to /dev/tty , which is unavailable to hooks To stop Claude entirely: { "continue" : false , "stopReason" : "Build failed, fix errors before continuing" } For PreToolUse and PostToolUse hooks, the stop applies even when the tool call fails or completes while Claude is still streaming a response.
​ Emit terminal notifications Hooks run without a controlling terminal, so writing escape sequences directly to /dev/tty fails.
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code writes the sequence itself when it processes your hook’s output, so the field works on events that discard systemMessage and continue , such as Notification and StopFailure .
It has two limits: Claude Code writes the sequence only in an interactive session, and only while its interface is on screen.
In non-interactive mode with the -p flag and in the Agent SDK, it ignores the field.
A WorktreeCreate command hook can’t return JSON, because Claude Code reads its stdout as the worktree path.
An HTTP WorktreeCreate hook returns JSON and can include the field.
- **removal** — removes a previously-present capability claim
  - was: On Windows, build the escape string in PowerShell or a script and emit the same JSON object.
terminalSequence is the supported replacement for hooks that previously wrote escape sequences directly to /dev/tty .
The allowlist is restricted to sequences that cannot move the cursor or alter colors, so a hook can never corrupt an on-screen prompt.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Claude reads the reminder on the next model request, but it does not appear as a chat message in the interface.
  - now: Claude reads the reminder on the next model request, but it doesn’t appear as a chat message in the interface.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Once injected, the text is saved in the session transcript.
For mid-session events like PostToolUse or UserPromptSubmit , resuming with --continue or --resume replays the saved text rather than re-running the hook for past turns, so values like timestamps or commit SHAs become stale on resume.
SessionStart hooks run again on resume with source set to "resume" , so they can refresh their context.
  - now: Claude Code saves the injected text in the session transcript.
For mid-session events like PostToolUse or UserPromptSubmit , when you resume with --continue or --resume , Claude Code replays the saved text rather than re-running the hook for past turns, so values like timestamps or commit SHAs become stale.
SessionStart hooks run again on resume with source set to "resume" , or "fork" if you added --fork-session , so they can refresh their context.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Stop and SubagentStop also accept hookSpecificOutput.additionalContext for non-error feedback that continues the conversation TeammateIdle, TaskCreated, TaskCompleted Exit code or continue: false Exit code 2 blocks the action with stderr feedback.
JSON {"continue": false, "stopReason": "..."} also stops the teammate entirely, matching Stop hook behavior PreToolUse hookSpecificOutput permissionDecision (allow/deny/ask/defer), permissionDecisionReason PermissionRequest hookSpecificOutput decision.behavior (allow/deny) PermissionDenied hookSpecificOutput retry: true tells the model it may retry the denied tool call WorktreeCreate path return Command hook prints path on stdout; HTTP hook returns hookSpecificOutput.worktreePath .
  - now: Stop and SubagentStop also accept hookSpecificOutput.additionalContext for non-error feedback that continues the conversation TeammateIdle, TaskCompleted Exit code or continue: false Exit code 2 blocks the action with stderr feedback.
JSON {"continue": false, "stopReason": "..."} also stops the teammate entirely, matching Stop hook behavior TaskCreated Exit code or top-level decision Exit code 2 or decision: "block" cancels the task and returns the message to Claude.
continue: false is ignored PreToolUse hookSpecificOutput permissionDecision (allow/deny/ask/defer), permissionDecisionReason PermissionRequest hookSpecificOutput decision.behavior (allow/deny) PermissionDenied hookSpecificOutput retry: true tells the model it may retry the denied tool call; Claude Code ignores it for no-verdict denials WorktreeCreate path return Command hook prints path on stdout; HTTP hook returns hookSpecificOutput.worktreePath .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: No blocking or decision control WorktreeRemove, Notification, SessionEnd, PostCompact, InstructionsLoaded, StopFailure, CwdChanged, FileChanged None No decision control.
  - now: No blocking or decision control WorktreeRemove, Notification, SessionEnd, PostCompact, InstructionsLoaded, StopFailure, CwdChanged, DirectoryAdded, FileChanged None No decision control.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: See PostToolUse decision control UserPromptSubmit : cannot replace the prompt; it only injects additionalContext alongside it For redaction or transformation use cases, intercept at PreToolUse for outbound tool inputs and PostToolUse for inbound tool results.
Here are examples of each pattern in action: Top-level decision PreToolUse PermissionRequest Used by UserPromptSubmit , UserPromptExpansion , PostToolUse , PostToolUseFailure , PostToolBatch , Stop , SubagentStop , ConfigChange , and PreCompact .
The only value is "block" .
  - now: See PostToolUse decision control UserPromptSubmit : can’t replace the prompt; it only injects additionalContext alongside it For redaction or transformation use cases, intercept at PreToolUse for outbound tool inputs and PostToolUse for inbound tool results.
Here are examples of each pattern in action: Top-level decision PreToolUse PermissionRequest The only value for decision is "block" .
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
  - now: The matcher value corresponds to how the session was initiated: Matcher When it fires startup New session resume --resume , --continue , or /resume clear /clear compact Auto or manual compaction fork A new session forked from an existing one: --fork-session with --resume or --continue , the /fork background copy, or /branch Before v2.1.214, forked sessions reported source "resume" .
​ SessionStart input In addition to the common input fields , SessionStart hooks receive source and optionally model , agent_type , and session_title : Field Description source How the session started: "startup" for new sessions, "resume" for resumed sessions, "clear" after /clear , "compact" after compaction, or "fork" for a new session forked from an existing one model The active model identifier.
It can be omitted, for example after /clear or when a session is restored through conversation recovery, so check for the field before reading it agent_type The agent name, present when you start Claude Code with claude --agent <name> session_title The current session title if one is already set, for example via --name or /rename .
A hook that emits sessionTitle can check session_title first to avoid overwriting a title the user set explicitly { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SessionStart" , "source" : "startup" , "model" : "claude-sonnet-5" } ​ SessionStart decision control Claude Code adds stdout it treats as plain text to Claude’s context.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Applies in non-interactive mode ( -p ), where it becomes the first turn even if no prompt is provided.
  - now: Applies in non-interactive mode with the -p flag, where it becomes the first turn even if no prompt is provided.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Applies only when source is "startup" or "resume" ; ignored on "clear" and "compact" watchPaths Array of absolute paths to watch for FileChanged events during this session reloadSkills Boolean.
  - now: Applies when source is "startup" , "resume" , or "fork" ; ignored on "clear" and "compact" watchPaths Array of absolute paths to watch for FileChanged events during this session reloadSkills Boolean.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use the JSON form when you need to combine context with other fields such as suppressOutput or sessionTitle .
  - now: Use the JSON form when you need to combine context with other fields such as sessionTitle .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This example syncs a shared skills repository and requests the re-scan: #!/bin/bash git -C ~/.claude/skills/team-skills pull --quiet 2> /dev/null || \ git clone --quiet https://git.example.com/your-org/team-skills.git ~/.claude/skills/team-skills echo '{"hookSpecificOutput": {"hookEventName": "SessionStart", "reloadSkills": true}}' ​ Persist environment variables SessionStart hooks have access to the CLAUDE_ENV_FILE environment variable, which provides a file path where you can persist environment variables for subsequent Bash commands.
  - now: This example syncs a shared skills repository and requests the re-scan: #!/bin/bash git -C ~/.claude/skills/team-skills pull --quiet 2> /dev/null || \ git clone --quiet https://git.example.com/your-org/team-skills.git ~/.claude/skills/team-skills echo '{"hookSpecificOutput": {"hookEventName": "SessionStart", "reloadSkills": true}}' The repository URL is a placeholder; replace it with your own skills repository.
With the placeholder, the clone fails and prints a fatal: message to stderr.
Stderr from a SessionStart hook that exits 0 is informational only, so the reloadSkills request still applies.
​ Persist environment variables SessionStart hooks have access to the CLAUDE_ENV_FILE environment variable, which provides a file path where you can persist environment variables for subsequent Bash commands.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use append ( >> ) to preserve variables set by other hooks: #!/bin/bash if [ -n " $CLAUDE_ENV_FILE " ]; then echo 'export NODE_ENV=production' >> " $CLAUDE_ENV_FILE " echo 'export DEBUG_LOG=true' >> " $CLAUDE_ENV_FILE " echo 'export PATH="$PATH:./node_modules/.bin"' >> " $CLAUDE_ENV_FILE " fi exit 0 To capture all environment changes from setup commands, compare the exported variables before and after: #!/bin/bash ENV_BEFORE = $(e xport -p | sort ) # Run your setup commands that modify the environment source ~/.nvm/nvm.sh nvm use 20 if [ -n " $CLAUDE_ENV_FILE " ]; then ENV_AFTER = $(e xport -p | sort ) comm -13 <( echo " $ENV_BEFORE ") <( echo " $ENV_AFTER ") >> " $CLAUDE_ENV_FILE " fi exit 0 Any variables written to this file will be available in all subsequent Bash commands that Claude Code executes during the session.
CLAUDE_ENV_FILE is available for SessionStart, Setup , CwdChanged , and FileChanged hooks.
Other hook types do not have access to this variable.
​ Setup Fires only when you launch Claude Code with --init-only , or with --init or --maintenance in print mode ( -p ).
It does not fire on normal startup.
  - now: Use append ( >> ) to preserve variables set by other hooks: #!/bin/bash if [ -n " $CLAUDE_ENV_FILE " ]; then echo 'export NODE_ENV=production' >> " $CLAUDE_ENV_FILE " echo 'export DEBUG_LOG=true' >> " $CLAUDE_ENV_FILE " echo 'export PATH="$PATH:./node_modules/.bin"' >> " $CLAUDE_ENV_FILE " fi exit 0 To capture all environment changes from setup commands, compare the exported variables before and after: #!/bin/bash ENV_BEFORE = $(e xport -p | sort ) # Run your setup commands that modify the environment source ~/.nvm/nvm.sh nvm use 20 if [ -n " $CLAUDE_ENV_FILE " ]; then ENV_AFTER = $(e xport -p | sort ) comm -13 <( echo " $ENV_BEFORE ") <( echo " $ENV_AFTER ") >> " $CLAUDE_ENV_FILE " fi exit 0 CLAUDE_ENV_FILE is available for SessionStart, Setup , CwdChanged , and FileChanged hooks.
Other hook types don’t have access to this variable.
​ Setup Fires only when you launch Claude Code with --init-only , or with --init or --maintenance in non-interactive mode with the -p flag.
It doesn’t fire on normal startup.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The matcher value corresponds to the CLI flag that triggered the hook: Matcher When it fires init claude --init-only or claude -p --init maintenance claude -p --maintenance --init-only runs Setup hooks and SessionStart hooks with the startup matcher, then exits without starting a conversation.
--init and --maintenance fire Setup hooks only when combined with -p (print mode); in an interactive session those two flags do not currently fire Setup hooks.
Because Setup does not fire on every launch, a plugin that needs a dependency installed cannot rely on Setup alone.
  - now: The matcher value corresponds to the CLI flag that triggered the hook: Matcher When it fires init claude --init-only or claude -p --init maintenance claude -p --maintenance When you run claude --init-only , Claude Code runs Setup hooks and SessionStart hooks with the startup matcher, then exits without starting a conversation.
When you start or continue a conversation with -p , you also need to supply a prompt, as an argument or piped on stdin.
You can skip the prompt when a SessionStart hook supplies initialUserMessage or when you resume a session with a deferred tool call .
On success, --init-only prints nothing to the terminal.
To confirm the hooks ran, start with claude --debug-file <path> --init-only , replacing <path> with a log file location, and check the log for the Setup and SessionStart hook entries.
Because Setup doesn’t fire on every launch, a plugin that needs a dependency installed can’t rely on Setup alone.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Setup input In addition to the common input fields , Setup hooks receive a trigger field set to either "init" or "maintenance" : { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Setup" , "trigger" : "init" } ​ Setup decision control Setup hooks cannot block.
On exit code 2, stderr is shown to the user; on any other non-zero exit code, stderr appears only when you launch with --verbose .
In both cases execution continues.
  - now: If you distribute your plugin through a marketplace, you may not need this pattern: Claude Code installs eligible Node.js package dependencies automatically when it caches the plugin.
​ Setup input In addition to the common input fields , Setup hooks receive a trigger field set to either "init" or "maintenance" : { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Setup" , "trigger" : "init" } ​ Setup decision control Setup hooks can’t block; execution continues on any exit code.
Exit code 2 surfaces stderr to the user as a <hook name> hook error notice whether or not you print JSON.
On any other non-zero exit, Claude Code applies the other exit codes rule: with a parsed object that passes schema validation it honors the fields and doesn’t report the hook as an error, and with anything else on stdout it shows that notice.
In non-interactive mode , hook output appears only when you launch with --verbose .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The hook does not support blocking or decision control.
  - now: The hook doesn’t support blocking or decision control.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: They cannot block or modify instruction loading.
  - now: They can’t block or modify instruction loading.
Claude Code discards their JSON output fields , such as systemMessage and continue .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: A UserPromptSubmit hook that reaches its timeout is canceled and its output, including any additionalContext , is discarded.
  - now: A UserPromptSubmit command, HTTP, or MCP tool hook that reaches its timeout is canceled and its output, including any additionalContext , is discarded.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: As of v2.1.196, the transcript shows a notice naming the hook, the timeout that fired, and that the output was discarded.
Earlier versions cancel the hook with no notice.
  - now: The transcript shows a notice naming the hook, the timeout that fired, and that the output was discarded.
An Agent SDK callback hook on UserPromptSubmit that reaches its timeout blocks the prompt with a message naming the hook and the timeout, because a callback there can be acting as a policy gate that must not fail open.
The session continues.
Before v2.1.208, a callback timeout on that event ended the turn with an execution error.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: There are two ways to add context to the conversation on exit code 0: Plain text stdout : any non-JSON text written to stdout is added as context JSON with additionalContext : use the JSON format below for more control.
The additionalContext field is added as context Plain stdout is shown as hook output in the transcript.
The additionalContext field is added more discretely.
  - now: There are two ways to add context to the conversation on exit code 0: Plain text stdout : Claude Code adds stdout it treats as plain text to Claude’s context JSON with additionalContext : use the JSON format below for more control.
The additionalContext field is added as context Neither channel produces a visible transcript entry.
Plain stdout and the additionalContext value are each injected as a system reminder that starts with the hook’s name; Claude reads both.
To confirm delivery, check the debug log .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use to name sessions automatically based on the prompt content suppressOriginalPrompt If true when decision is "block" , omits the original prompt text from the block message shown to the user { "decision" : "block" , "reason" : "Explanation for decision" , "hookSpecificOutput" : { "hookEventName" : "UserPromptSubmit" , "additionalContext" : "My additional context here" , "sessionTitle" : "My session title" } } The JSON format isn’t required for simple use cases.
To add context, you can print plain text to stdout with exit code 0.
Use JSON when you need to block prompts or want more structured control.
​ UserPromptExpansion Runs when a user-typed slash command expands into a prompt before reaching Claude.
  - now: Use to name sessions automatically based on the prompt content suppressOriginalPrompt If true when decision is "block" , omits the original prompt text from the block message shown to the user A hook that blocks by exiting 2 routes the same way as reason : the block message shows the stderr text to the user, and it isn’t added to context.
{ "decision" : "block" , "reason" : "Explanation for decision" , "hookSpecificOutput" : { "hookEventName" : "UserPromptSubmit" , "additionalContext" : "My additional context here" , "sessionTitle" : "My session title" } } ​ UserPromptExpansion Runs when a user-typed command expands into a prompt before reaching Claude.
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
  - was: See Add context for Claude { "decision" : "block" , "reason" : "This slash command is not available" , "hookSpecificOutput" : { "hookEventName" : "UserPromptExpansion" , "additionalContext" : "Additional context for this expansion" } } ​ MessageDisplay Runs while an assistant message streams to the screen.
  - now: See Add context for Claude A hook that blocks by exiting 2 routes the same way as reason : the block message shows the stderr text to the user.
{ "decision" : "block" , "reason" : "This slash command is not available" , "hookSpecificOutput" : { "hookEventName" : "UserPromptExpansion" , "additionalContext" : "Additional context for this expansion" } } ​ MessageDisplay Runs while an assistant message streams to the screen.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: MessageDisplay does not support matchers and fires for every assistant message that streams text; messages with no text, such as tool-call-only responses, do not trigger it.
  - now: MessageDisplay doesn’t support matchers and fires for every assistant message that streams text; messages with no text, such as tool-call-only responses, don’t trigger it.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: This is not the API msg_… id, so it cannot be correlated with transcript message ids index Zero-based index of this batch within the message final true on the message’s last batch.
  - now: This is not the API msg_… id, so it can’t be correlated with transcript message ids index Zero-based index of this batch within the message final true on the message’s last batch.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block the message or change what is stored in the transcript or sent to Claude.
  - now: They can’t block the message or change what is stored in the transcript or sent to Claude.
Claude Code acts on displayContent from their JSON output and discards systemMessage and continue .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: macOS/Linux Windows (PowerShell) Register a command hook for the event in your settings file: { "hooks" : { "MessageDisplay" : [ { "hooks" : [ { "type" : "command" , "command" : "${CLAUDE_PROJECT_DIR}/.claude/hooks/plain-display.sh" , "args" : [] } ] } ] } } Save this script to .claude/hooks/plain-display.sh in your project and make it executable with chmod +x : #!/bin/bash jq '{hookSpecificOutput: {hookEventName: "MessageDisplay", displayContent: (.delta | gsub("\\*\\*"; "") | gsub("`"; ""))}}' The script needs jq on your PATH .
Register a command hook that runs the script through PowerShell: { "hooks" : { "MessageDisplay" : [ { "hooks" : [ { "type" : "command" , "command" : "powershell.exe" , "args" : [ "-NoProfile" , "-ExecutionPolicy" , "Bypass" , "-File" , "${CLAUDE_PROJECT_DIR}/.claude/hooks/plain-display.ps1" ] } ] } ] } } The -NoProfile flag skips loading your PowerShell profile so the hook starts fast, and -ExecutionPolicy Bypass lets PowerShell run the local script file.
  - now: macOS/Linux Windows (PowerShell) Register a command hook for the event in your settings file: { "hooks" : { "MessageDisplay" : [ { "hooks" : [ { "type" : "command" , "command" : "${CLAUDE_PROJECT_DIR}/.claude/hooks/plain-display.sh" , "args" : [] } ] } ] } } Save this script to .claude/hooks/plain-display.sh in your project and make it executable with chmod +x : #!/bin/bash jq '{hookSpecificOutput: {hookEventName: "MessageDisplay", displayContent: (.delta | gsub("\\*\\*"; "") | gsub("`"; ""))}}' Register a command hook that runs the script through PowerShell: { "hooks" : { "MessageDisplay" : [ { "hooks" : [ { "type" : "command" , "command" : "powershell.exe" , "args" : [ "-NoProfile" , "-ExecutionPolicy" , "Bypass" , "-File" , "${CLAUDE_PROJECT_DIR}/.claude/hooks/plain-display.ps1" ] } ] } ] } } The -NoProfile flag skips loading your PowerShell profile so the hook starts fast, and -ExecutionPolicy Bypass lets PowerShell run the local script file.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Matches on tool name: Bash , Edit , Write , Read , Glob , Grep , Agent , WebFetch , WebSearch , AskUserQuestion , ExitPlanMode , and any MCP tool names .
  - now: Matches on tool name: Bash , PowerShell , Edit , Write , Read , Glob , Grep , Agent , WebFetch , WebSearch , AskUserQuestion , ExitPlanMode , and any MCP tool names .
- **new-claim** — adds a capability claim not previously upstream
  - now: PreToolUse also doesn’t fire for EndConversation .
- **new-claim** — adds a capability claim not previously upstream
  - now: An Agent SDK callback hook on PreToolUse that exceeds its timeout blocks the tool call, and Claude receives an error result naming the timeout.
An explicit deny returned by another hook still takes precedence.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The tool_input fields depend on the tool: Bash Executes shell commands.
Field Type Example Description command string "npm test" The shell command to execute description string "Run test suite" Optional description of what the command does timeout number 120000 Optional timeout in milliseconds run_in_background boolean false Whether to run the command in background Write Creates or overwrites a file.
  - now: For the file tools Write , Edit , and Read , tool_input.file_path is always absolute: Claude Code expands ~ and relative paths before hooks run, so a hook that matches on paths can’t be bypassed via ~ or a relative spelling of the same path On Windows, the path arrives with backslash separators, even when your hook runs under Git Bash where $PWD looks like /c/project A comparison written with forward slashes, such as a /src/ check, never matches a backslash path, and the tool call proceeds as if the hook had nothing to block Normalize separators before comparing: FILE_PATH="${FILE_PATH//\\//}" in Bash, or file_path.replace("\\", "/") in Python, then match a path segment such as /src/ rather than anchoring with ^ , since the path is absolute A Write call on Windows delivers: { "hook_event_name" : "PreToolUse" , "tool_name" : "Write" , "tool_input" : { "file_path" : "C: \\ project \\ src \\ index.ts" , "content" : "..." }, ...
} The tool_input fields depend on the tool: Bash Executes shell commands.
Field Type Example Description command string "npm test" The shell command to execute description string "Run test suite" Optional description of what the command does timeout number 120000 Optional timeout in milliseconds.
Values above the maximum are reduced to the maximum rather than rejected run_in_background boolean false Whether to run the command in background PowerShell Executes PowerShell commands.
See the PowerShell tool for availability by platform.
The fields match the Bash tool, with the command string in command : Field Type Example Description command string "Get-ChildItem -Recurse" The PowerShell command to execute description string "List files recursively" Optional description of what the command does timeout number 120000 Optional timeout in milliseconds run_in_background boolean false Whether to run the command in background Match Bash|PowerShell in hooks that inspect shell commands, so they cover both tools: On Windows, wherever the PowerShell tool is enabled, Claude treats PowerShell as the primary shell and routes shell commands through it.
On Windows without Git Bash, the tool is enabled automatically and Claude Code doesn’t register the Bash tool at all.
A hook that matches only Bash never fires there.
Write Creates or overwrites a file.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Field Type Example Description prompt string "Find all API endpoints" The task for the agent to perform description string "Find API endpoints" Short description of the task subagent_type string "Explore" Type of specialized agent to use model string "sonnet" Optional model alias to override the default In PostToolUse , tool_response for a completed Agent call carries the subagent’s final text along with usage telemetry.
Read these fields to record per-subagent cost from a hook: Field Type Example Description status string "completed" "completed" for synchronous calls, "async_launched" for run_in_background: true agentId string "a4d2c8f1e0b3a297" Identifier for the subagent run content array [{"type": "text", "text": "Found 12 endpoints..."}] The subagent’s final text blocks resolvedModel string "claude-sonnet-4-5" Model the subagent ran on, which may differ from the requested model.
Requires Claude Code v2.1.174 or later totalTokens number 12450 Total tokens billed across the subagent’s turns totalDurationMs number 48211 Wall-clock duration of the subagent run totalToolUseCount number 7 Count of tool calls the subagent made usage object {"input_tokens": 8320, ...} Per-type token breakdown: input_tokens , output_tokens , cache_creation_input_tokens , cache_read_input_tokens For run_in_background: true calls, the tool returns immediately after launching the subagent, so tool_response carries no usage fields.
  - now: Field Type Example Description prompt string "Find all API endpoints" The task for the agent to perform description string "Find API endpoints" Short description of the task subagent_type string "Explore" Type of specialized agent to use model string "sonnet" Optional model alias to override the default When a foreground Agent call completes, your PostToolUse hook receives the subagent’s final text and run telemetry in tool_response .
Read these fields to inspect the run; for token and cost rollups across subagents, use the token and cost counters filtered to query_source "subagent" , since totalTokens and usage cover the final request only: Field Type Example Description status string "completed" "completed" for foreground subagents, "async_launched" for background subagents.
As of v2.1.198, subagents run in the background by default, so an omitted run_in_background also produces "async_launched" agentId string "a4d2c8f1e0b3a297" Identifier for the subagent run content array [{"type": "text", "text": "Found 12 endpoints..."}] The subagent’s final text blocks resolvedModel string "claude-sonnet-4-5" Model the subagent started on, which may differ from the requested model.
Requires Claude Code v2.1.174 or later modelsUsed array ["claude-sonnet-4-5", "claude-haiku-4-5"] Models used in order, with consecutive repeats collapsed; set only when the model was swapped mid-run.
Requires Claude Code v2.1.212 or later totalTokens number 12450 Token count from the subagent’s final API request: input, output, and cache tokens combined.
This isn’t a total across the whole run totalDurationMs number 48211 Wall-clock duration of the subagent run totalToolUseCount number 7 Count of tool calls the subagent made usage object {"input_tokens": 8320, ...} Per-type token breakdown of the final API request: input_tokens , output_tokens , cache_creation_input_tokens , cache_read_input_tokens For background subagents, the tool returns when the task moves to the background, so tool_response carries no usage fields: a background launch returns immediately, and a foreground task that Claude Code backgrounds mid-run returns at that transition.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The resolvedModel field names the model the subagent actually runs on, which can differ from the model value in tool_input , such as when availableModels or another override applies.
  - now: On a completed response, resolvedModel names the model the subagent started on, which can differ from the model value in tool_input , such as when availableModels or another override applies.
- **new-claim** — adds a capability claim not previously upstream
  - now: On an async_launched response, resolvedModel names the model in use when the agent moved to the background, so a swap that happened before backgrounding is reflected there.
modelsUsed and the backgrounding-time resolvedModel behavior require Claude Code v2.1.212 or later.
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
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Field Description permissionDecision "allow" skips the permission prompt.
  - now: Field Description permissionDecision "allow" skips the permission prompt, except for tools that require user interaction and connector tools your organization set to ask .
- **new-claim** — adds a capability claim not previously upstream
  - now: A hook that blocks by exiting 2 routes the same way as "deny" : Claude sees the stderr message as the denial reason.
- **new-claim** — adds a capability claim not previously upstream
  - now: A hook’s "ask" also forces a permission prompt in auto mode : the classifier can still deny the tool call, but it can’t approve the call silently.
Before v2.1.211, the classifier could approve a Bash command running outside the sandbox without showing the prompt the hook requested; the classifier still applied its own safety rules to that command, and a hook "deny" was always honored.
- **new-claim** — adds a capability claim not previously upstream
  - now: As of v2.1.199, an MCP tool whose server marks it with _meta["anthropic/requiresUserInteraction"] is stricter: a hook can’t skip its approval prompt with "allow" , with or without updatedInput , because Claude Code can’t confirm the hook collected the interaction the tool needs.
- **removal** — removes a previously-present capability claim
  - was: The defer value requires Claude Code v2.1.89 or later.
Earlier versions do not recognize it and the tool proceeds through the normal permission flow.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The tool does not execute.
  - now: The tool doesn’t execute.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The session remains on disk until you resume it, subject to the cleanupPeriodDays retention sweep that deletes session files after 30 days by default.
  - now: The session remains on disk until you resume it, subject to the cleanupPeriodDays retention sweep, which deletes session files after 30 days by default, following the retention sweep rules .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: --resume restores the permission mode that was active when the tool was deferred, so you do not need to pass --permission-mode again.
The exceptions are plan and bypassPermissions , which are never carried over.
  - now: --resume restores the permission mode that was active when the tool was deferred, so you don’t need to pass --permission-mode again.
The exceptions are plan and bypassPermissions , which are never carried over, and auto , which is restored only when your account still meets the auto mode requirements .
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ PermissionRequest Runs when the user is shown a permission dialog.
  - now: ​ PermissionRequest Runs when Claude Code is about to ask you for permission.
In sessions that can’t show a prompt, such as background subagents in non-interactive mode , Claude Code still runs these hooks, and if no hook returns a decision, it denies the tool call.
- **new-claim** — adds a capability claim not previously upstream
  - now: Use this event when you need a signal the moment Claude asks for permission.
The Notification event’s permission_prompt type reaches you only after about 6 seconds without terminal input.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The difference is when the hook fires: PermissionRequest hooks run when a permission dialog is about to be shown to the user, while PreToolUse hooks run before tool execution regardless of permission status.
  - now: PreToolUse hooks run before every tool call, whether or not it needs permission.
PermissionRequest hooks run only when Claude Code is about to ask you for permission, or when it would otherwise auto-deny a call that can’t prompt.
Neither event fires for EndConversation .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Deny and ask rules are still evaluated, so a hook returning "allow" does not override a matching deny rule updatedInput For "allow" only: modifies the tool’s input parameters before execution.
  - now: Deny and ask rules are still evaluated, so a hook returning "allow" doesn’t override a matching deny rule updatedInput For "allow" only: modifies the tool’s input parameters before execution.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The modified input is re-evaluated against deny and ask rules updatedPermissions For "allow" only: array of permission update entries to apply, such as adding an allow rule or changing the session permission mode message For "deny" only: tells Claude why the permission was denied interrupt For "deny" only: if true , stops Claude { "hookSpecificOutput" : { "hookEventName" : "PermissionRequest" , "decision" : { "behavior" : "allow" , "updatedInput" : { "command" : "npm run lint" } } } } ​ Permission update entries The updatedPermissions output field and the permission_suggestions input field both use the same array of entry objects.
  - now: The modified input is re-evaluated against deny and ask rules updatedPermissions For "allow" only: array of permission update entries to apply, such as adding an allow rule or changing the session permission mode message For "deny" only: tells Claude why the permission was denied interrupt For "deny" only: if true , stops Claude A hook that exits 2 without a decision object leaves the permission flow unchanged, and its stderr is discarded.
Only the decision object can grant or deny the request.
{ "hookSpecificOutput" : { "hookEventName" : "PermissionRequest" , "decision" : { "behavior" : "allow" , "updatedInput" : { "command" : "npm run lint" } } } } ​ Permission update entries The updatedPermissions output field and the permission_suggestions input field both use the same array of entry objects.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Valid modes are default , auto , acceptEdits , dontAsk , bypassPermissions , and plan addDirectories directories , destination Adds working directories.
  - now: Valid modes are default , auto , acceptEdits , dontAsk , bypassPermissions , plan , and manual as an alias for default .
The manual alias requires Claude Code v2.1.200 or later addDirectories directories , destination Adds working directories.
- **new-claim** — adds a capability claim not previously upstream
  - now: File-tool tool_input paths arrive in the same format as for PreToolUse : always absolute, with the platform’s native separators, so backslashes on Windows.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For built-in tools, a value that does not match the tool’s output schema is ignored and the original output is used.
  - now: For built-in tools, a value that doesn’t match the tool’s output schema is ignored and the original output is used.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ PostToolUseFailure Runs when a tool execution fails.
This event fires for tool calls that throw errors or return failure results.
  - now: ​ PostToolUseFailure Runs when a tool that started executing fails: the tool threw an error, or an MCP tool returned an error result.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ PostToolUseFailure input PostToolUseFailure hooks receive the same tool_name and tool_input fields as PostToolUse, along with error information as top-level fields: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "PostToolUseFailure" , "tool_name" : "Bash" , "tool_input" : { "command" : "npm test" , "description" : "Run test suite" }, "tool_use_id" : "toolu_01ABC123..." , "error" : "Command exited with non-zero status code 1" , "is_interrupt" : false , "duration_ms" : 4187 } Field Description error String describing what went wrong is_interrupt Optional boolean indicating whether the failure was caused by user interruption duration_ms Optional.
  - now: This event doesn’t fire for tool calls rejected before execution: an unknown tool name, input that fails schema or tool-specific validation, or a permission denial.
Validation rejections are returned as tool_use_error results and happen before hooks run, so they fire neither PreToolUse nor PostToolUseFailure .
Permission denials fire PreToolUse but not this event; see PermissionDenied .
​ PostToolUseFailure input PostToolUseFailure hooks receive the same tool_name and tool_input fields as PostToolUse, along with error information as top-level fields.
For example, a failed npm test command might deliver: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "PostToolUseFailure" , "tool_name" : "Bash" , "tool_input" : { "command" : "npm test" , "description" : "Run test suite" }, "tool_use_id" : "toolu_01ABC123..." , "error" : "Exit code 1 \n Error: Cannot find module 'express'" , "is_interrupt" : false , "duration_ms" : 4187 } Field Description error String describing what went wrong.
The format depends on the tool that failed is_interrupt Optional boolean.
True when the failure reached Claude Code as an abort rather than as an error the tool reported.
Cancelling a running tool does not fire this hook; the tool result carries the interruption message instead duration_ms Optional.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Excludes time spent in permission prompts and PreToolUse hooks ​ PostToolUseFailure decision control PostToolUseFailure hooks can provide context to Claude after a tool failure.
  - now: Excludes time spent in permission prompts and PreToolUse hooks The error string is generally the same text Claude receives as the failed tool’s result.
Its format varies by tool and failure.
Key your hook on tool_name , is_interrupt , and the Exit code N first line; treat the rest of the string as display text, not a stable format.
For Bash and PowerShell, a command that ran and exited produces a first line Exit code N , then any output the command produced as one block with stdout and stderr interleaved A payload may also carry a bare failure message with no exit-code line, when Claude Code could not start the shell process itself Claude Code middle-truncates strings longer than 10,000 characters around a ...
[N characters truncated] ...
marker, and can insert lines of its own, such as Command timed out after 2m 0s ​ PostToolUseFailure decision control PostToolUseFailure hooks can provide context to Claude after a tool failure.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ PermissionDenied Runs when the auto mode classifier denies a tool call.
This hook only fires in auto mode: it does not run when you manually deny a permission dialog, when a PreToolUse hook blocks a call, or when a deny rule matches.
Use it to log classifier denials, adjust configuration, or tell the model it may retry the tool call.
  - now: The blocking message comes from the JSON reason or stopReason , or from stderr on exit 2.
You see it as a warning in the transcript, and it stays in the conversation, so Claude sees it when the conversation continues.
​ PermissionDenied Runs when auto mode denies a tool call, including when it denies without a classifier verdict because a safety check separate from auto mode refused the classifier’s own request or its response didn’t parse.
This hook only fires in auto mode: it doesn’t run when you manually deny a permission dialog, when a PreToolUse hook blocks a call, or when a deny rule matches.
Use it to log denials, adjust configuration, or tell the model it may retry the tool call.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "auto" , "hook_event_name" : "PermissionDenied" , "tool_name" : "Bash" , "tool_input" : { "command" : "rm -rf /tmp/build" , "description" : "Clean build directory" }, "tool_use_id" : "toolu_01ABC123..." , "reason" : "Auto mode denied: command targets a path outside the project" } Field Description reason The classifier’s explanation for why the tool call was denied ​ PermissionDenied decision control PermissionDenied hooks can tell the model it may retry the denied tool call.
  - now: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "auto" , "hook_event_name" : "PermissionDenied" , "tool_name" : "Bash" , "tool_input" : { "command" : "rm -rf /tmp/build" , "description" : "Clean build directory" }, "tool_use_id" : "toolu_01ABC123..." , "reason" : "Blocked by classifier" } Field Description reason The denial reason: the fixed text Blocked by classifier in most sessions, or the classifier’s written explanation when the session’s classifier model provides one.
For a denial where a safety check separate from auto mode refused the classifier’s request or its response didn’t parse, the reason starts with Auto mode could not evaluate this action and is blocking it for safety .
For a denial because the classifier model was unavailable, the reason is the fixed text Classifier unavailable .
See Review denials ​ PermissionDenied decision control PermissionDenied hooks can tell the model it may retry the denied tool call.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The denial itself is not reversed.
If your hook does not return JSON, or returns retry: false , the denial stands and the model receives the original rejection message.
  - now: Claude Code doesn’t reverse the denial itself.
If your hook doesn’t return JSON, or returns retry: false , the denial stands and the model receives the original rejection message.
Claude Code ignores retry: true when the classifier produced no verdict on the action : its response didn’t parse, or a safety check separate from auto mode refused the classifier’s own request.
For those denials, Claude Code already tells the model in the rejection message whether to retry later or move on.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Matches on notification type: permission_prompt , idle_prompt , auth_success , elicitation_dialog , elicitation_complete , elicitation_response .
  - now: Matches on notification type.
- **new-claim** — adds a capability claim not previously upstream
  - now: You receive these hook events even with desktop notifications turned off: the preferredNotifChannel setting, including notifications_disabled , changes only how you’re alerted, not whether your hook runs.
Matcher When it fires permission_prompt Claude needs you to approve a tool use and you haven’t typed for about 6 seconds idle_prompt Claude finished responding about 60 seconds ago and you haven’t typed since auth_success Authentication completes elicitation_dialog An MCP server opens an elicitation form and you haven’t typed for about 6 seconds elicitation_url_dialog An MCP server asks you to open a browser URL and you haven’t typed for about 6 seconds elicitation_complete An MCP elicitation form is submitted or dismissed elicitation_response An MCP elicitation response is sent back to the server agent_needs_input A background session starts waiting on your input.
Fires only while agent view is open in a terminal agent_completed A background session finishes or fails.
Fires only while agent view is open in a terminal The agent_needs_input and agent_completed types require Claude Code v2.1.198 or later.
The permission_prompt , idle_prompt , elicitation_dialog , and elicitation_url_dialog types share their timing with desktop notifications, so you only see them when you appear to be away from the terminal: Expect permission_prompt once you haven’t typed for about 6 seconds.
The timer starts when the permission prompt appears, and each keystroke defers it.
To run a hook immediately on every permission ask, use PermissionRequest instead.
Expect idle_prompt about 60 seconds after Claude finishes responding, and only if you haven’t typed since.
Expect elicitation_dialog for an elicitation form, or elicitation_url_dialog for a browser URL request, once you haven’t typed for about 6 seconds.
Both share the same 6-second gate as permission_prompt : the timer starts when the dialog appears, and each keystroke defers it.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Notification" , "message" : "Claude needs your permission" , "title" : "Permission needed" , "notification_type" : "permission_prompt" } Notification hooks cannot block or modify notifications.
They are intended for side effects such as forwarding the notification to an external service.
The common JSON output fields such as systemMessage apply.
  - now: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "Notification" , "message" : "Claude needs your permission" , "title" : "Permission needed" , "notification_type" : "permission_prompt" } Notification hooks can’t block or modify notifications.
Claude Code discards their systemMessage and continue fields but still emits terminalSequence , which is what the desktop notification example relies on.
Notification hooks are intended for side effects such as forwarding the notification to an external service.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ SubagentStart input In addition to the common input fields , SubagentStart hooks receive agent_id with the unique identifier for the subagent and agent_type with the agent name (built-in agents like "general-purpose" , "Explore" , "Plan" , or custom agent names).
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SubagentStart" , "agent_id" : "agent-abc123" , "agent_type" : "Explore" } SubagentStart hooks cannot block subagent creation, but they can inject context into the subagent.
  - now: ​ SubagentStart input In addition to the common input fields , SubagentStart hooks receive agent_id with the unique identifier for the subagent and agent_type with the agent name that the matcher filters on.
{ "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "hook_event_name" : "SubagentStart" , "agent_id" : "agent-abc123" , "agent_type" : "Explore" } SubagentStart hooks can’t block subagent creation, but they can inject context into the subagent.
- **new-claim** — adds a capability claim not previously upstream
  - now: A hook that blocks by exiting 2 delivers its stderr message the same way.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: When a TaskCreated hook exits with code 2, the task is not created and the stderr message is fed back to the model as feedback.
To stop the teammate entirely instead of re-running it, return JSON with {"continue": false, "stopReason": "..."} .
TaskCreated hooks do not support matchers and fire on every occurrence.
  - now: In a session without the Task tools , this event doesn’t fire.
TaskCreated hooks don’t support matchers and fire on every occurrence.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Session-derived team name; will be removed in a future release ​ TaskCreated decision control TaskCreated hooks support two ways to control task creation: Exit code 2 : the task is not created and the stderr message is fed back to the model as feedback.
JSON {"continue": false, "stopReason": "..."} : stops the teammate entirely, matching Stop hook behavior.
The stopReason is shown to the user.
  - now: Session-derived team name; will be removed in a future release ​ TaskCreated decision control A TaskCreated hook can block the creation in two ways.
Either way, Claude Code deletes the task and returns your message to Claude as the tool’s error.
Claude Code ignores continue: false from this event and Claude keeps working.
Exit code 2 : Claude Code returns the stderr text as the message.
JSON {"decision": "block", "reason": "..."} : Claude Code returns reason as the message.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: When a TaskCompleted hook exits with code 2, the task is not marked as completed and the stderr message is fed back to the model as feedback.
To stop the teammate entirely instead of re-running it, return JSON with {"continue": false, "stopReason": "..."} .
TaskCompleted hooks do not support matchers and fire on every occurrence.
  - now: TaskCompleted hooks don’t support matchers and fire on every occurrence.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Use it when you want Claude to keep working until a condition holds without writing hook configuration.
  - now: Use it when you want Claude to keep working toward a condition without writing hook configuration.
- **new-claim** — adds a capability claim not previously upstream
  - now: For hooks that act on the just-completed turn, such as read-aloud or notification hooks, use this field rather than reading transcript_path : the transcript file isn’t guaranteed to include the final message at Stop time on all versions.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The conversation continues so Claude can act on it, but unlike decision: "block" it is shown in the transcript as hook feedback rather than a hook error { "decision" : "block" , "reason" : "Must be provided when Claude is blocked from stopping" } Use additionalContext when the hook is working as designed and giving Claude guidance, such as “run the test suite before finishing”.
  - now: The conversation continues so Claude can act on it, but unlike decision: "block" it is shown in the transcript as hook feedback rather than a hook error A hook that blocks by exiting 2 routes the same way as reason : Claude receives the stderr message as the explanation for why it should continue.
{ "decision" : "block" , "reason" : "Must be provided when Claude is blocked from stopping" } Use additionalContext when the hook is working as designed and giving Claude guidance, such as “run the test suite before finishing”.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Output and exit code are ignored.
Use this to log failures, send alerts, or take recovery actions when Claude cannot complete a response due to rate limits, authentication problems, or other API errors.
  - now: Claude Code ignores the hook’s output and exit code, apart from terminalSequence .
Use this to log failures, send alerts, or take recovery actions when Claude can’t complete a response due to rate limits, authentication problems, or other API errors.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: When a TeammateIdle hook exits with code 2, the teammate receives the stderr message as feedback and continues working instead of going idle.
To stop the teammate entirely instead of re-running it, return JSON with {"continue": false, "stopReason": "..."} .
TeammateIdle hooks do not support matchers and fire on every occurrence.
  - now: TeammateIdle hooks don’t support matchers and fire on every occurrence.
- **removal** — removes a previously-present capability claim
  - was: The source field in the input tells you which type of configuration changed, and the optional file_path field provides the path to the changed file.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Omit to allow the change reason Explanation shown to the user when decision is "block" { "decision" : "block" , "reason" : "Configuration changes to project settings require admin approval" } policy_settings changes cannot be blocked.
  - now: Omit to allow the change reason Accepted but never shown { "decision" : "block" , "reason" : "Configuration changes to project settings require admin approval" } policy_settings changes can’t be blocked.
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code acts on the blocking decision from a ConfigChange hook’s JSON output and discards systemMessage and continue .
A blocked change surfaces no message to you or to Claude, whether you block with reason or with stderr on exit 2.
Claude Code only writes a line to the debug log.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: CwdChanged does not support matchers and fires on every directory change.
  - now: CwdChanged doesn’t support matchers and fires on every directory change.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Replaces the current dynamic watch list (paths from your matcher configuration are always watched).
  - now: Replaces the current dynamic watch list.
Paths from your matcher configuration are always watched.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: They cannot block the directory change.
​ FileChanged Runs when a watched file changes on disk.
  - now: They can’t block the directory change.
Claude Code reads watchPaths and systemMessage from their JSON output and discards continue .
In interactive sessions, it shows the systemMessage as a brief terminal notification.
The message doesn’t reach the SDK message stream.
​ DirectoryAdded Runs after you add a working directory mid-session with the /add-dir command, or after an SDK client adds one with the register_repo_root control request.
Use this to prepare a newly added repository, for example by installing its dependencies.
Claude Code doesn’t fire this event when: You pass a directory with the --add-dir startup flag; SessionStart covers those directories You add a directory on the /permissions Workspace tab You add a directory that is already a working directory; the add fails with an error Claude Code fires DirectoryAdded after refreshing sandbox and permission state, so sandboxed tools already see the new directory when your hook runs.
Hook commands themselves run unsandboxed.
Claude Code doesn’t wait for the hook: the add completes immediately, and the hook runs in the background with the 600-second default timeout.
The matcher filters on how the directory was added: Matcher When it fires slash_command You add a directory with /add-dir register_repo_root An SDK client adds a directory with the register_repo_root control request ​ DirectoryAdded input In addition to the common input fields , DirectoryAdded hooks receive directory and source .
Field Description directory Absolute path of the directory that was added source How the directory was added, "slash_command" for /add-dir or "register_repo_root" for the SDK control request { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../transcript.jsonl" , "cwd" : "/Users/my-project" , "hook_event_name" : "DirectoryAdded" , "directory" : "/Users/my-other-repo" , "source" : "slash_command" } DirectoryAdded hooks have no decision control.
They can’t block the add, which has already completed when the hook runs.
Claude Code discards the continue field from their JSON output and surfaces the rest differently per source: slash_command : Claude Code delivers the hook’s systemMessage to Claude as context on the next conversation turn, rather than showing it to you.
A count of failed hooks appears in the transcript.
Full failure output goes to the debug log register_repo_root : Claude Code writes systemMessage output and failure output to the debug log only ​ FileChanged Runs when a watched file changes on disk.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Field Description file_path Absolute path to the file that changed event What happened: "change" (file modified), "add" (file created), or "unlink" (file deleted) { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../transcript.jsonl" , "cwd" : "/Users/my-project" , "hook_event_name" : "FileChanged" , "file_path" : "/Users/my-project/.envrc" , "event" : "change" } ​ FileChanged output In addition to the JSON output fields available to all hooks, FileChanged hooks can return watchPaths to dynamically update which file paths are watched: Field Description watchPaths Array of absolute paths.
Replaces the current dynamic watch list (paths from your matcher configuration are always watched).
  - now: Field Description file_path Absolute path to the file that changed event What happened: "change" for a modified file, "add" for a created file, or "unlink" for a deleted file { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../transcript.jsonl" , "cwd" : "/Users/my-project" , "hook_event_name" : "FileChanged" , "file_path" : "/Users/my-project/.envrc" , "event" : "change" } ​ FileChanged output In addition to the JSON output fields available to all hooks, FileChanged hooks can return watchPaths to dynamically update which file paths are watched: Field Description watchPaths Array of absolute paths.
Replaces the current dynamic watch list.
Paths from your matcher configuration are always watched.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: They cannot block the file change from occurring.
​ WorktreeCreate When you run claude --worktree or a subagent uses isolation: "worktree" , Claude Code creates an isolated working copy using git worktree .
If you configure a WorktreeCreate hook, it replaces the default git behavior, letting you use a different version control system like SVN, Perforce, or Mercurial.
  - now: They can’t block the file change from occurring.
Claude Code reads watchPaths and systemMessage from their JSON output and discards continue .
In interactive sessions, it shows the systemMessage as a brief terminal notification.
The message doesn’t reach the SDK message stream.
​ WorktreeCreate Runs when a worktree is being created, whether from claude --worktree , from a subagent using isolation: "worktree" , or for a background session that Claude Code isolates in its own worktree.
By default Claude Code creates the isolated working copy with git worktree .
Configuring a WorktreeCreate hook replaces that default git behavior, letting you use a different version control system like SVN, Perforce, or Mercurial.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The hook must return the absolute path to the created worktree directory.
  - now: The hook must return the path to the created worktree directory.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Command hooks print it on stdout; HTTP hooks return it via hookSpecificOutput.worktreePath .
  - now: See WorktreeCreate output for how each hook type returns the path.
Claude Code acts on the hook’s success and the returned path, and discards systemMessage and continue .
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
  - now: Claude Code resolves a relative path against the directory the hook ran in, collapsing any .
or ..
segments in it.
If the resulting path isn’t a directory Claude Code can enter, the session prints an error naming the path and exits with code 1.
Claude Code refuses an absolute path that contains .
or ..
segments, and any path that passes through a symlink below the repository root, because a symlink committed to the repository could redirect the worktree outside it.
The error names the rejected component.
Return a normalized path that doesn’t pass through a symlink inside the repository.
Before v2.1.216, worktree creation followed the hook’s path without this screening.
​ WorktreeRemove Runs when a worktree is being removed.
This is the cleanup counterpart to WorktreeCreate .
The event fires when: you exit a --worktree session and choose to remove it a subagent with isolation: "worktree" finishes you delete a background session whose worktree the hook created For git-based worktrees, Claude Code handles cleanup automatically with git worktree remove .
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code discards a WorktreeRemove hook’s JSON output fields , such as systemMessage and continue .
For a background-session delete, Claude Code verifies the stored worktree path before running the hook and refuses a path that is a symlink or passes through one below the repository root.
The hook runs for a worktree that still contains files only when you confirm the delete in agent view ; for such a worktree, claude rm keeps the session and worktree instead.
Before v2.1.216, the hook ran on the stored path without these checks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block worktree removal but can perform cleanup tasks like removing version control state or archiving changes.
  - now: They can’t block worktree removal but can perform cleanup tasks like removing version control state or archiving changes.
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code discards a PreCompact hook’s systemMessage and continue fields.
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code discards a PostCompact hook’s systemMessage and continue fields.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot affect the compaction result but can perform follow-up tasks.
  - now: They can’t affect the compaction result but can perform follow-up tasks.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: They cannot block session termination but can perform cleanup tasks.
  - now: They can’t block session termination but can perform cleanup tasks.
Claude Code discards their JSON output fields , such as systemMessage .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Timeouts set on plugin-provided hooks do not raise the budget.
  - now: Timeouts set on plugin-provided hooks don’t raise the budget.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: For form-mode elicitation (the most common case): { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please provide your credentials" , "mode" : "form" , "requested_schema" : { "type" : "object" , "properties" : { "username" : { "type" : "string" , "title" : "Username" } } } } For URL-mode elicitation (browser-based authentication): { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please authenticate" , "mode" : "url" , "url" : "https://auth.example.com/login" } ​ Elicitation output To respond programmatically without showing the dialog, return a JSON object with hookSpecificOutput : { "hookSpecificOutput" : { "hookEventName" : "Elicitation" , "action" : "accept" , "content" : { "username" : "alice" } } } Field Values Description action accept , decline , cancel Whether to accept, decline, or cancel the request content object Form field values to submit.
Only used when action is accept Exit code 2 denies the elicitation and shows stderr to the user.
  - now: For form-mode elicitation, the most common case: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please provide your credentials" , "mode" : "form" , "requested_schema" : { "type" : "object" , "properties" : { "username" : { "type" : "string" , "title" : "Username" } } } } For URL-mode elicitation, used for browser-based authentication: { "session_id" : "abc123" , "transcript_path" : "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl" , "cwd" : "/Users/..." , "permission_mode" : "default" , "hook_event_name" : "Elicitation" , "mcp_server_name" : "my-mcp-server" , "message" : "Please authenticate" , "mode" : "url" , "url" : "https://auth.example.com/login" } ​ Elicitation output To respond programmatically without showing the dialog, return a JSON object with hookSpecificOutput : { "hookSpecificOutput" : { "hookEventName" : "Elicitation" , "action" : "accept" , "content" : { "username" : "alice" } } } Field Values Description action accept , decline , cancel Whether to accept, decline, or cancel the request content object Form field values to submit.
Only used when action is accept Exit code 2 denies the elicitation.
Claude Code doesn’t show your stderr message anywhere.
Claude Code acts on hookSpecificOutput from an Elicitation hook’s JSON output and discards systemMessage and continue .
- **new-claim** — adds a capability claim not previously upstream
  - now: Claude Code doesn’t show your stderr message anywhere.
Claude Code acts on hookSpecificOutput from an ElicitationResult hook’s JSON output and discards systemMessage and continue .
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Events that support all five hook types ( command , http , mcp_tool , prompt , and agent ): PermissionDenied PermissionRequest PostToolBatch PostToolUse PostToolUseFailure PreToolUse Stop SubagentStop TaskCompleted TaskCreated TeammateIdle UserPromptExpansion UserPromptSubmit Events that support command , http , and mcp_tool hooks but not prompt or agent : ConfigChange CwdChanged Elicitation ElicitationResult FileChanged InstructionsLoaded Notification PostCompact PreCompact SessionEnd StopFailure SubagentStart WorktreeCreate WorktreeRemove SessionStart and Setup support command and mcp_tool hooks.
They do not support http , prompt , or agent hooks.
  - now: Events that support all five hook types ( command , http , mcp_tool , prompt , and agent ): PermissionDenied PermissionRequest PostToolBatch PostToolUse PostToolUseFailure PreToolUse Stop SubagentStop TaskCompleted TaskCreated TeammateIdle UserPromptExpansion UserPromptSubmit Events that support command , http , and mcp_tool hooks but not prompt or agent : ConfigChange CwdChanged DirectoryAdded Elicitation ElicitationResult FileChanged InstructionsLoaded MessageDisplay Notification PostCompact PreCompact SessionEnd StopFailure SubagentStart WorktreeCreate WorktreeRemove SessionStart and Setup support command and mcp_tool hooks.
They don’t support http , prompt , or agent hooks.
- **removal** — removes a previously-present capability claim
  - was: Claude Code sends the combined prompt and input to a fast Claude model, which returns a JSON decision.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Default: 30 continueOnBlock no When the prompt returns ok: false , feed the reason back to Claude and continue the turn instead of stopping.
  - now: Default: 30 continueOnBlock no On the events it applies to, true feeds an ok: false reason back to Claude and continues instead of ending the turn.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Implemented as continue: true on the resulting decision: "block" .
See Response schema for per-event behavior ​ Response schema The LLM must respond with JSON containing: { "ok" : true | false , "reason" : "Explanation for the decision" } Field Description ok true to allow.
false produces a decision: "block" .
See the per-event behavior below reason Required when ok is false .
Used as the block reason What happens on ok: false depends on the event: Stop and SubagentStop : the reason is fed back to Claude as its next instruction and the turn continues PreToolUse : the tool call is denied and the reason is returned to Claude as the tool error, equivalent to a command hook’s permissionDecision: "deny" PostToolUse : by default the turn ends and the reason appears in the chat as a warning line.
  - now: See Response schema for per-event behavior ​ Response schema The LLM must respond with JSON containing: { "ok" : true | false , "reason" : "Explanation for the decision" , "impossible" : true | false } Field Description ok true to allow.
For false , see the per-event behavior below reason Required when ok is false impossible Optional.
The model returns it with ok: false when it judges the condition can never be satisfied.
On Stop and SubagentStop , Claude Code then lets the turn end instead of feeding the reason back.
Agent hooks and other events ignore it What happens on ok: false depends on the event: Stop and SubagentStop : the reason is fed back to Claude as its next instruction and the turn continues, unless the response also sets impossible: true , in which case Claude Code allows the stop and the turn ends PreToolUse : the tool call is denied; by default the turn ends and the deny reason appears in the chat as a warning line.
Set continueOnBlock: true to instead return the reason to Claude as the tool error so it can adjust and continue, equivalent to a command hook’s permissionDecision: "deny" .
Before v2.1.210, the deny reason was returned to Claude as the tool error and the turn continued PostToolUse : by default the turn ends and the reason appears in the chat as a warning line.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: These events end the turn on decision: "block" regardless of continue PostToolUseFailure , TaskCreated , and TaskCompleted : the reason is returned to Claude as a tool error, similar to PreToolUse TeammateIdle : by default the teammate stops and the reason appears as a warning line.
  - now: These events end the turn on decision: "block" regardless of continue PostToolUseFailure and TaskCreated : the reason is returned to Claude as a tool error and the turn continues, regardless of continueOnBlock TaskCompleted : when it fires because a task is marked completed during a turn, the reason is returned to Claude as a tool error and the turn continues, regardless of continueOnBlock .
When it fires because a teammate stops, it behaves like TeammateIdle and halts the teammate by default TeammateIdle : by default the teammate stops and the reason appears as a warning line.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The only output this event reads is hookSpecificOutput.retry , which prompt and agent hooks cannot set.
  - now: The only output this event reads is hookSpecificOutput.retry , which prompt and agent hooks can’t set.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ Example: Multi-criteria Stop hook This Stop hook uses a detailed prompt to check three conditions before allowing Claude to stop.
If "ok" is false , Claude continues working with the provided reason as its next instruction.
SubagentStop hooks use the same format to evaluate whether a subagent should stop: { "hooks" : { "Stop" : [ { "hooks" : [ { "type" : "prompt" , "prompt" : "You are evaluating whether Claude should stop working.
  - now: ​ Check multiple conditions before stopping This Stop hook uses a detailed prompt to check three conditions before allowing Claude to stop.
SubagentStop hooks use the same format to evaluate whether a subagent should stop.
If the model returns "ok": false because the condition isn’t met yet, Claude continues working with the provided reason as its next instruction: { "hooks" : { "Stop" : [ { "hooks" : [ { "type" : "prompt" , "prompt" : "You are evaluating whether Claude should stop working.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ How agent hooks work When an agent hook fires: Claude Code spawns a subagent with your prompt and the hook’s JSON input The subagent can use tools like Read, Grep, and Glob to investigate After up to 50 turns, the subagent returns a structured { "ok": true/false } decision Claude Code processes the decision the same way as a prompt hook Agent hooks are useful when verification requires inspecting actual files or test output, not just evaluating the hook input data alone.
  - now: ​ How agent hooks work When an agent hook fires: Claude Code spawns a subagent with your prompt and the hook’s JSON input The subagent can use tools like Read, Grep, and Glob to investigate After up to 50 turns, the subagent returns a structured { "ok": true/false } decision Claude Code allows the action if ok is true .
If ok is false , Claude Code handles the block the same way as a prompt hook with continueOnBlock: true on that event, as listed under Response schema Agent hooks are useful when verification requires inspecting actual files or test output, not just evaluating the hook input data alone.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The configuration fields are the same as prompt hooks , with a longer default timeout: Field Required Description type yes Must be "agent" prompt yes Prompt describing what to verify.
  - now: The configuration fields are the same as prompt hooks , except that agent hooks have a longer default timeout and no continueOnBlock field: Field Required Description type yes Must be "agent" prompt yes Prompt describing what to verify.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Default: 60 The response schema is the same as prompt hooks: { "ok": true } to allow or { "ok": false, "reason": "..." } to block.
  - now: Default: 60 The response schema is { "ok": true } to allow or { "ok": false, "reason": "..." } to block.
On ok: false , Claude Code handles an agent hook the way it handles a prompt hook with continueOnBlock: true on the same event; agent hooks have no continueOnBlock field, and don’t support the prompt-hook impossible field.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: Async hooks cannot block or control Claude’s behavior: response fields like decision , permissionDecision , and continue have no effect, because the action they would have controlled has already completed.
  - now: Async hooks can’t block or control Claude’s behavior: response fields like decision , permissionDecision , and continue have no effect, because the action they would have controlled has already completed.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ​ How async hooks execute When an async hook fires, Claude Code starts the hook process and immediately continues without waiting for it to finish.
  - now: Claude Code delivers an async hook’s results only while the session runs: In non-interactive mode with the -p flag, Claude Code kills any async hook still running at teardown and finalizes it with outcome cancelled If your hook’s work must outlive a claude -p session, start a fully detached process from it ​ How async hooks execute When an async hook fires, Claude Code starts the hook process and immediately continues without waiting for it to finish.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: After the background process exits, if the hook produced a JSON response with an additionalContext field, that content is delivered to Claude as context on the next conversation turn.
A systemMessage field is shown to you, not to Claude.
  - now: After the background process exits, Claude Code delivers the additionalContext and systemMessage fields from the hook’s JSON response to Claude on the next conversation turn.
Unlike a synchronous hook’s systemMessage , neither field is shown to you.
Claude Code validates that JSON response against the same output schema as synchronous hooks, and drops any field whose value has the wrong type, such as a systemMessage that isn’t a string, instead of delivering it.
Run with --debug to see a warning naming each dropped field.
Before v2.1.202, malformed JSON output from an async hook could crash the session, and the crash recurred each time the session was resumed.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Example: run tests after file changes This hook starts a test suite in the background whenever Claude writes a file, then reports the results back to Claude when the tests finish.
  - now: ​ Run tests after file changes This hook starts a test suite in the background whenever Claude writes a file, then reports the results back to Claude when the tests finish.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: The async: true flag lets Claude keep working while tests run: { "hooks" : { "PostToolUse" : [ { "matcher" : "Write|Edit" , "hooks" : [ { "type" : "command" , "command" : "${CLAUDE_PROJECT_DIR}/.claude/hooks/run-tests-async.sh" , "args" : [], "async" : true , "timeout" : 300 } ] } ] } } ​ Limitations Async hooks have several constraints compared to synchronous hooks: Only type: "command" hooks support async .
Prompt-based hooks cannot run asynchronously.
Async hooks cannot block tool calls or return decisions.
By the time the hook completes, the triggering action has already proceeded.
Hook output is delivered on the next conversation turn.
  - now: The async: true flag lets Claude keep working while tests run: { "hooks" : { "PostToolUse" : [ { "matcher" : "Write|Edit" , "hooks" : [ { "type" : "command" , "command" : "${CLAUDE_PROJECT_DIR}/.claude/hooks/run-tests-async.sh" , "args" : [], "async" : true , "timeout" : 300 } ] } ] } } ​ Limitations Async hooks have additional constraints compared to synchronous hooks: Hook output is delivered on the next conversation turn.
- **curated-divergence** — upstream same-statement update could not auto-land: entry body has curatorially diverged from upstream
  - was: ​ Security considerations ​ Disclaimer Command hooks run with your system user’s full permissions.
Command hooks execute shell commands with your full user permissions.
  - now: ​ Security considerations ​ Disclaimer Command hooks execute shell commands with your full user permissions.
- **new-claim** — adds a capability claim not previously upstream
  - now: ​ Workspace trust Claude Code checks workspace trust before it runs any hook from a settings file.
What counts as trusted depends on the session type: Interactive session : Claude Code holds back hooks from every settings file, including your own ~/.claude/settings.json , until you accept the workspace trust dialog for the folder or one of its parent directories -p or SDK session : Claude Code never shows the dialog and treats the folder as trusted, so hooks committed in a repository’s .claude/settings.json run in a folder you’ve never trusted Before you script claude -p over a repository you didn’t write, review its .claude/ settings files, start with --bare , or turn hooks off for that run with --settings '{"disableAllHooks": true}' .
Frontmatter hooks in a project subagent follow a stricter rule than settings-file hooks.
What runs before you trust a folder lists each kind of repository content by session type.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Hooks spawn PowerShell directly, so this works regardless of whether CLAUDE_CODE_USE_POWERSHELL_TOOL is set.
Claude Code auto-detects pwsh.exe (PowerShell 7+) with a fallback to powershell.exe (5.1).
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
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: The --debug flag does not print to the terminal.
[DEBUG] Executing hooks for PostToolUse:Write [DEBUG] Found 1 hook commands to execute [DEBUG] Executing hook command: <Your command> with timeout 600000ms [DEBUG] Hook command completed with status 0: <Your stdout> For more granular hook matching details, set CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose to see additional log lines such as hook matcher counts and query matching.
  - now: The --debug flag doesn’t print to the terminal.
For example, a PostToolUse hook on Write whose command prints hook-ran produces entries like: 2026-07-19T02:03:24.382Z [DEBUG] Hook output does not start with {, treating as plain text 2026-07-19T02:03:24.382Z [DEBUG] Hook PostToolUse:Write (PostToolUse) success: hook-ran For more granular hook matching details, set CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose to see additional log lines such as hook matcher counts and query matching.
