# Pending delta — anthropic-pricing

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://platform.claude.com/docs/en/about-claude/pricing`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-21T13:04:59Z

- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Pricing - Claude Platform Docs Claude Platform Docs Messages Managed Agents Admin Resources   API reference English   Console Log in    Search...
⌘K Models Models overview Model IDs and versioning Choosing a model Introducing Claude Fable 5 and Claude Mythos 5 What's new in Claude Opus 4.8 What's new in Claude Sonnet 5 Upgrade between model versions Model deprecations Model cards System prompts Pricing  Log in  Models & pricing  Pricing Loading...
  - now: Pricing - Claude Platform Docs Claude Platform Docs Messages Managed Agents Admin Resources   API reference English   Console Log in    Search ⌘K Models Models overview Model IDs and versioning Choosing a model Introducing Claude Fable 5 and Claude Mythos 5 What's new in Claude Opus 4.8 What's new in Claude Sonnet 5 Upgrade between model versions Model deprecations Model cards System prompts Pricing  Log in  Models & pricing  Pricing Loading...
- **new-claim** — adds a capability claim not previously upstream
  - now: The exact increase depends on the content and workload shape.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was:  Specific tool pricing  Bash tool The bash tool adds 245 input tokens to your API calls.
Additional tokens are consumed by: Command outputs (stdout/stderr) Error messages Large file contents See tool use pricing for complete pricing details.
  - now:  Specific tool pricing  Bash tool The bash tool definition adds the following input tokens to your request.
This is in addition to the per-model tool use system prompt that applies whenever any tool is present.
Model Additional input tokens Claude Opus 4.7 and Claude Opus 4.8 325 tokens Claude Opus 4.6, Claude Sonnet 4.6, and earlier 244 tokens Additional tokens are consumed by: Command outputs (stdout/stderr) Error messages Large file contents See tool use pricing for complete pricing details.
- **reprojection** — same-statement update (similarity >= threshold)
  - was: When used without these tools, code execution is billed by execution time, tracked separately from token usage: Execution time has a minimum of 5 minutes Each organization receives 1,550 free hours of usage per month Additional usage beyond 1,550 hours is billed at $0.05 per hour, per container If files are included in the request, execution time is billed even if the tool is not invoked, due to files being preloaded onto the container Code execution usage is tracked in the response: { "usage" : { "input_tokens" : 105 , "output_tokens" : 239 , "server_tool_use" : { "code_execution_requests" : 1 } } }   Text editor tool The text editor tool uses the same pricing structure as other tools used with Claude.
  - now: When used without these tools, code execution is billed by execution time, tracked separately from token usage: Execution time has a minimum of 5 minutes Each organization receives 1,550 free hours of usage per month Additional usage beyond 1,550 hours is billed at $0.05 USD per hour, per container If files are included in the request, execution time is billed even if the tool is not called, because files are preloaded onto the container Code execution usage is tracked in the response: { "usage" : { "input_tokens" : 105 , "output_tokens" : 239 , "server_tool_use" : { "code_execution_requests" : 1 } } }   Text editor tool The text editor tool uses the same pricing structure as other tools used with Claude.
- **reprojection** — same-statement update (similarity >= threshold)
  - was: When using the computer use tool: System prompt overhead : The computer use beta adds 466-499 tokens to the system prompt Computer use tool token usage : Model Input tokens per tool definition Claude 4.x models 735 tokens Additional token consumption : Screenshot images (see Vision pricing ) Tool execution results returned to Claude  If you're also using bash or text editor tools alongside computer use, those tools have their own token costs as documented in their respective pages.
  - now: When using the computer use tool: System prompt overhead: The computer use beta adds 466–499 tokens to the system prompt Computer use tool token usage: Model Input tokens per tool definition Claude 4.x models 735 tokens Additional token consumption: Screenshot images (see Vision pricing ) Tool execution results returned to Claude  If you're also using bash or text editor tools alongside computer use, those tools have their own token costs as documented in their respective pages.
