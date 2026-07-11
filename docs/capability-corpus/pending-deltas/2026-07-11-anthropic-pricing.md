# Pending delta — anthropic-pricing

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://platform.claude.com/docs/en/about-claude/pricing`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-07-11T12:59:02Z

- **new-claim** — adds a capability claim not previously upstream
  - now: The exact increase depends on the content and workload shape.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was:  Specific tool pricing  Bash tool The bash tool adds 245 input tokens to your API calls.
Additional tokens are consumed by: Command outputs (stdout/stderr) Error messages Large file contents See tool use pricing for complete pricing details.
  - now:  Specific tool pricing  Bash tool The bash tool definition adds the following input tokens to your request.
This is in addition to the per-model tool use system prompt that applies whenever any tool is present.
Model Additional input tokens Claude Opus 4.7 and Claude Opus 4.8 325 tokens Claude Opus 4.6, Claude Sonnet 4.6, and earlier 244 tokens Additional tokens are consumed by: Command outputs (stdout/stderr) Error messages Large file contents See tool use pricing for complete pricing details.
