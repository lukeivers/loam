# Pending delta — anthropic-models-overview

> Review-class upstream changes surfaced by capability-refresh.
> Source: `https://platform.claude.com/docs/en/about-claude/models/overview.md`
> Projection target: `(watch source — no projection target)`
> These do NOT auto-land (D-CUR.4): new claims, removals, overlay
> touches, contradiction-suspects, and curated-divergences need review.

## Run 2026-08-31T19:13:25Z

- **new-claim** — adds a capability claim not previously upstream
  - now: ---
title: Models overview
url: https://platform.claude.com/docs/en/models/overview
description: Claude is a family of state-of-the-art large language models developed by Anthropic. This guide introduces the available models and compares their performance.
---
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude is a family of state-of-the-art large language models developed by Anthropic. This guide introduces the available models and compares their performance.
  - now: Claude is a family of state-of-the-art large language models developed by Anthropic. Compare the current lineup, find the model ID for every platform, and open each model's page for its full specs and resources.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ---
  - now: <HomeQuickChip icon="Signpost" href="https://platform.claude.com/docs/en/about-claude/models/choosing-a-model">
  Choosing a model
</HomeQuickChip>
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ## Choosing a model
  - now: <HomeQuickChip icon="DollarSign" href="https://platform.claude.com/docs/en/about-claude/pricing">
  Pricing
</HomeQuickChip>
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: If you're unsure which model to use, start with **Claude Opus 4.8** for complex agentic coding and enterprise work. For workloads that need the highest available capability, use [Claude Fable 5](#claude-fable-5-and-claude-mythos-5).
  - now: <HomeQuickChip icon="ArrowUpCircle" href="https://platform.claude.com/docs/en/about-claude/models/migration-guide">
  Migration guide
</HomeQuickChip>
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: All current Claude models support text and image input, text output, multilingual capabilities, and vision. Models are available through the Claude API, [Claude Platform on AWS](/docs/en/build-with-claude/claude-platform-on-aws), [Amazon Bedrock](/docs/en/build-with-claude/claude-in-amazon-bedrock), [Google Cloud](/docs/en/build-with-claude/claude-on-vertex-ai), and [Microsoft Foundry](/docs/en/build-with-claude/claude-in-microsoft-foundry).
  - now: ## Compare models
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Once you've picked a model, [learn how to make your first API call](/docs/en/get-started).
  - now: If you're unsure which model to use, start with [Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview) for complex agentic coding and enterprise work; for the highest available capability, use [Claude Fable 5](https://platform.claude.com/docs/en/models/fable-5/overview). All current models support text and image input, text output, multilingual capabilities, vision, and tool use; each model's page lists the platforms it is available on.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ### Claude Fable 5 and Claude Mythos 5
  - now: | Feature                                                                                                   | Claude Fable 5                                                                | Claude Opus 5                                                               | Claude Sonnet 5                                                                 | Claude Haiku 4.5                                                                  |
| :-------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------- | :-------------------------------------------------------------------------- | :------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------- |
| Description                                                                                               | Next-generation intelligence for long-running agents                          | For complex agentic coding and enterprise work                              | The best combination of speed and intelligence                                  | The fastest model with near-frontier intelligence                                 |
| Model page                                                                                                | [Claude Fable 5](https://platform.claude.com/docs/en/models/fable-5/overview) | [Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview) | [Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview) | [Claude Haiku 4.5](https://platform.claude.com/docs/en/models/haiku-4-5/overview) |
| Comparative latency                                                                                       | Slower                                                                        | Moderate                                                                    | Fast                                                                            | Fastest                                                                           |
| [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)                                       | $10 / input MTok, $50 / output MTok                                           | $5 / input MTok, $25 / output MTok                                          | $2 / input MTok, $10 / output MTok                                              | $1 / input MTok, $5 / output MTok                                                 |
| Claude API ID                                                                                             | `claude-fable-5`                                                              | `claude-opus-5`                                                             | `claude-sonnet-5`                                                               | `claude-haiku-4-5-20251001`                                                       |
| [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)                                | Adaptive (always on)                                                          | Adaptive                                                                    | Adaptive                                                                        | Extended                                                                          |
| [Default effort](https://platform.claude.com/docs/en/build-with-claude/effort)                            | `high`                                                                        | `high`                                                                      | `high`                                                                          | Not supported                                                                     |
| [Context window](https://platform.claude.com/docs/en/build-with-claude/context-windows)                   | 1M tokens                                                                     | 1M tokens                                                                   | 1M tokens                                                                       | 200K tokens                                                                       |
| Max output                                                                                                | 128K tokens                                                                   | 128K tokens                                                                 | 128K tokens                                                                     | 64K tokens                                                                        |
| Reliable knowledge cutoff                                                                                 | Jan 2026                                                                      | May 2026                                                                    | Jan 2026                                                                        | Feb 2025                                                                          |
| Training data cutoff                                                                                      | Jan 2026                                                                      | May 2026                                                                    | Jan 2026                                                                        | Jul 2025                                                                          |
| [Retirement](https://platform.claude.com/docs/en/about-claude/model-deprecations)                         | Not sooner than June 9, 2027                                                  | Not sooner than July 24, 2027                                               | Not sooner than June 30, 2027                                                   | Not sooner than October 15, 2026                                                  |
| Claude API alias                                                                                          | `claude-fable-5`                                                              | `claude-opus-5`                                                             | `claude-sonnet-5`                                                               | `claude-haiku-4-5`                                                                |
| [Amazon Bedrock ID](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)       | `anthropic.claude-fable-5`                                                    | `anthropic.claude-opus-5`                                                   | `anthropic.claude-sonnet-5`                                                     | `anthropic.claude-haiku-4-5`                                                      |
| [Google Cloud ID](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)              | `claude-fable-5`                                                              | `claude-opus-5`                                                             | `claude-sonnet-5`                                                               | `claude-haiku-4-5@20251001`                                                       |
| [Microsoft Foundry ID](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) | `claude-fable-5`                                                              | `claude-opus-5`                                                             | `claude-sonnet-5`                                                               | `claude-haiku-4-5`                                                                |
| [Claude Platform on AWS ID](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws) | `claude-fable-5`                                                              | —                                                                           | `claude-sonnet-5`                                                               | `claude-haiku-4-5`                                                                |
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude Fable 5 (`claude-fable-5`) is Anthropic's most capable widely released model. Claude Mythos 5 (`claude-mythos-5`) shares Claude Fable 5's specs and pricing and joins the invitation-only Claude Mythos Preview (`claude-mythos-preview`) within [Project Glasswing](https://anthropic.com/glasswing). See [Introducing Claude Fable 5 and Claude Mythos 5](/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5) for launch details and API changes.
  - now: * **Comparative latency:** Relative to the current lineup. Actual latency depends on prompt length, output length, and thinking effort.
* **Pricing:** Base price per million tokens. Batch API requests are 50% off; prompt cache reads cost 10% of the base input price. See Pricing for cache writes, long-context, and per-platform pricing.
* **Claude API ID:** Every Claude model ID is a pinned snapshot, including the dateless IDs used from the 4.6 generation on.
* **Thinking:** Adaptive thinking lets the model decide how much to think, steered by effort. Extended thinking is the manual thinking.type “enabled” + budget\_tokens mode on earlier models; it is deprecated on Claude Opus 4.6 and Claude Sonnet 4.6 and not accepted on later models.
* **Default effort:** The effort parameter’s default on the Claude API. Set effort explicitly to use a different level.
* **Context window:** 1M tokens is roughly 555k words or 2.5M Unicode characters on the current tokenizer (introduced with Claude Opus 4.7); models before it fit about 750k words in 1M tokens. 200k tokens is roughly 150k words.
* **Max output:** Synchronous Messages API limit. On the Message Batches API, Claude Opus 5, Claude Sonnet 5, Claude Opus 4.8, Claude Opus 4.7, Claude Opus 4.6, and Claude Sonnet 4.6 support up to 300k output tokens with the output-300k-2026-03-24 beta header.
* **Reliable knowledge cutoff:** The date through which the model’s knowledge is most extensive and reliable. Training data cutoff (under Show all details) is the broader range of data used. See Anthropic’s Transparency Hub for details.
* **Retirement:** Anthropic’s commitment for Anthropic-operated platforms (Claude API, Claude Platform on AWS, Microsoft Foundry). Amazon Bedrock and Google Cloud set their own dates.
* **Claude API alias:** For models before the 4.6 generation, the alias is a convenience pointer that resolves to the dated ID. Dateless IDs are their own pinned snapshot; the alias row repeats them.
* **Amazon Bedrock ID:** The ID on Bedrock’s Messages-API endpoint (Claude Opus 4.7 and later, plus Claude Haiku 4.5); a model offered only through Bedrock’s InvokeModel integration shows that ID instead. Bedrock offers global endpoints (dynamic routing) and regional endpoints (guaranteed data routing) for Claude Sonnet 4.5 and later, and sets its own lifecycle dates.
* **Google Cloud ID:** Google Cloud offers global, multi-region, and regional endpoints, and sets its own lifecycle dates.
* **Microsoft Foundry ID:** Foundry deployments default to the Claude API model ID (the alias, where one exists); the deployment name is what you send. Foundry follows the Claude API lifecycle schedule.
* **Claude Platform on AWS ID:** Claude Platform on AWS uses the Claude API model IDs (the dateless form where the Claude API has an alias), not Bedrock-style IDs, and follows Anthropic’s first-party model lifecycle.
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: Claude Fable 5 is generally available on the Claude API, Claude Platform on AWS, Amazon Bedrock, Google Cloud, and Microsoft Foundry beginning June 9, 2026. Claude Mythos 5 is not generally available: it is offered in limited availability to approved customers in [Project Glasswing](https://anthropic.com/glasswing), beginning the same day. For access, contact your Anthropic, AWS, or Google Cloud account team.
  - now: See [Model IDs and versioning](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions) and [Pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: ### Latest models comparison
  - now: Legacy models (still available): [Claude Opus 4.8](https://platform.claude.com/docs/en/models/opus-4-8/overview), [Claude Opus 4.7](https://platform.claude.com/docs/en/models/opus-4-7/overview), [Claude Opus 4.6](https://platform.claude.com/docs/en/models/opus-4-6/overview), [Claude Opus 4.5](https://platform.claude.com/docs/en/models/opus-4-5/overview), [Claude Sonnet 4.6](https://platform.claude.com/docs/en/models/sonnet-4-6/overview), [Claude Sonnet 4.5](https://platform.claude.com/docs/en/models/sonnet-4-5/overview).
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: | Feature                                                               | Claude Fable 5                                                                                                                                                                                                                                      | Claude Opus 4.8                                                                      | Claude Sonnet 5                                                                      | Claude Haiku 4.5                                                                       |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| **Description**                                                       | Next-generation intelligence for long-running agents                                                                                                                                                                                                | For complex agentic coding and enterprise work                                       | The best combination of speed and intelligence                                       | The fastest model with near-frontier intelligence                                      |
| **Claude API ID**                                                     | claude-fable-5                                                                                                                                                                                                                                      | claude-opus-4-8                                                                      | `claude-sonnet-5`                                                                    | claude-haiku-4-5-20251001                                                              |
| **Claude API alias**                                                  | claude-fable-5                                                                                                                                                                                                                                      | claude-opus-4-8                                                                      | `claude-sonnet-5`                                                                    | claude-haiku-4-5                                                                       |
| **AWS Bedrock ID**                                                    | anthropic.claude-fable-53                                                                                                                                                                                                                           | anthropic.claude-opus-4-83                                                           | `anthropic.claude-sonnet-5`3                                                         | anthropic.claude-haiku-4-5-20251001-v1:0                                               |
| **Google Cloud ID**                                                   | claude-fable-5                                                                                                                                                                                                                                      | claude-opus-4-8                                                                      | `claude-sonnet-5`                                                                    | claude-haiku-4-5\@20251001                                                             |
| **Pricing**1                                                          | $10 / input MTok $50 / output MTok                                                                                                                                                                                                                  | $5 / input MTok $25 / output MTok                                                    | $3 / input MTok $15 / output MTok4                                                   | $1 / input MTok $5 / output MTok                                                       |
| **[Extended thinking](/docs/en/build-with-claude/extended-thinking)** | No                                                                                                                                                                                                                                                  | No                                                                                   | No                                                                                   | Yes                                                                                    |
| **[Adaptive thinking](/docs/en/build-with-claude/adaptive-thinking)** | Yes (always on)                                                                                                                                                                                                                                     | Yes                                                                                  | Yes                                                                                  | No                                                                                     |
| **Comparative latency**                                               | Slower                                                                                                                                                                                                                                              | Moderate                                                                             | Fast                                                                                 | Fastest                                                                                |
| **Context window**                                                    | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters. Claude Fable 5 uses the tokenizer introduced with Claude Opus 4.7; compared to models before Claude Opus 4.7, the same text produces roughly 30% more tokens.">1M tokens</Tooltip> | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters">1M tokens</Tooltip> | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters">1M tokens</Tooltip> | <Tooltip tooltipContent="~150k words \ ~680k unicode characters">200k tokens</Tooltip> |
| **Max output**                                                        | 128k tokens                                                                                                                                                                                                                                         | 128k tokens                                                                          | 128k tokens                                                                          | 64k tokens                                                                             |
| **Reliable knowledge cutoff**                                         | Jan 20262                                                                                                                                                                                                                                           | Jan 20262                                                                            | Jan 20262                                                                            | Feb 2025                                                                               |
| **Training data cutoff**                                              | Jan 2026                                                                                                                                                                                                                                            | Jan 2026                                                                             | Jan 2026                                                                             | Jul 2025                                                                               |
  - now: Once you've picked a model, [learn how to make your first API call](https://platform.claude.com/docs/en/get-started). For how model IDs, aliases, and snapshots work, see [Model IDs and versioning](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions); for the reliable-knowledge and training-data cutoffs behind each model, see [Anthropic's Transparency Hub](https://www.anthropic.com/transparency).
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: *1 - See [Pricing](/docs/en/about-claude/pricing) for complete pricing information including Batch API discounts and prompt caching rates.*
  - now: ## Using the Models API
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: *2 - **Reliable knowledge cutoff** indicates the date through which a model's knowledge is most extensive and reliable. **Training data cutoff** is the broader date range of training data used. For more information, see [Anthropic's Transparency Hub](https://www.anthropic.com/transparency).*

*3 - Claude Fable 5, Claude Opus 4.8, and Claude Sonnet 5 are available on Bedrock through [Claude in Amazon Bedrock](/docs/en/build-with-claude/claude-in-amazon-bedrock) (the Messages-API Bedrock endpoint).*

*4 - Introductory pricing of $2 / $10 per MTok applies to Claude Sonnet 5 through August 31, 2026. See [Pricing](/docs/en/about-claude/pricing#claude-sonnet-5-introductory-pricing).*

<Info>
  Claude Mythos 5 and Claude Mythos Preview are offered separately for defensive cybersecurity workflows as part of [Project Glasswing](https://anthropic.com/glasswing). Access is invitation-only and there is no self-serve sign-up.
</Info>

<Note>
  Every Claude model ID is a pinned snapshot. Models with a date in the ID (for example,

  `20250929`

  ) are fixed to that specific release. Starting with the Claude 4.6 generation, model IDs use a dateless format that is also a pinned snapshot, not an evergreen pointer. For models before the 4.6 generation, entries in the Claude API alias column are convenience pointers that resolve to a dated model ID. For details on the naming convention and how versioning works, see

  [Model IDs and versioning](/docs/en/about-claude/models/model-ids-and-versions)

  .
</Note>

<Note>
  Starting with

  **Claude Sonnet 4.5 and all subsequent models**

   (including Claude Sonnet 4.6), Bedrock offers two endpoint types:

  **global endpoints**

   (dynamic routing for maximum availability) and

  **regional endpoints**

   (guaranteed data routing through specific geographic regions). Google Cloud offers three endpoint types: global endpoints,

  **multi-region endpoints**

   (dynamic routing within a geographic area), and regional endpoints. For more information, see

  [Cloud platform pricing](/docs/en/about-claude/pricing#cloud-platform-pricing)

  .
</Note>

<Note>
  **Claude Platform on AWS**

   uses the same model IDs as the Claude API (for example,

  `claude-opus-4-6`

  ), not Bedrock-style IDs. Model lifecycle on Claude Platform on AWS follows Anthropic's first-party

  [Model deprecations](/docs/en/about-claude/model-deprecations)

  , not Bedrock's. See

  [Available models](/docs/en/build-with-claude/claude-platform-on-aws#available-models)

   for the model list.
</Note>

<Tip>
  You can query model capabilities and token limits programmatically with the [Models API](/docs/en/api/models/list). The response includes `max_input_tokens`, `max_tokens`, and a `capabilities` object for every available model.
</Tip>

<Note>
  On Claude Opus 4.8, the `effort` parameter defaults to `high` on all surfaces, including the Claude API, Claude Code, and claude.ai. On Claude Sonnet 5, it defaults to `high` on the Claude API and Claude Code. Set `effort` explicitly to use a different level. See [Effort](/docs/en/build-with-claude/effort) for guidance on choosing a level.
</Note>

<Note>
  The Max output values above apply to the synchronous Messages API. On the [Message Batches API](/docs/en/build-with-claude/batch-processing#extended-output-beta), Claude Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5, and Sonnet 4.6 support up to 300k output tokens by using the `output-300k-2026-03-24` beta header.
</Note>

<AccordionGroup>
  <Accordion title="Legacy models">
    The following models are still available. Consider migrating to current models for improved performance:

    | Feature                                                               | Claude Opus 4.7                                                                                                      | Claude Opus 4.6                                                                      | Claude Sonnet 4.6                                                                    | Claude Sonnet 4.5                                                                      | Claude Opus 4.5                                                                        | Claude Opus 4.1 (deprecated)                                                           |
    | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
    | **Claude API ID**                                                     | claude-opus-4-7                                                                                                      | claude-opus-4-6                                                                      | claude-sonnet-4-6                                                                    | claude-sonnet-4-5-20250929                                                             | claude-opus-4-5-20251101                                                               | claude-opus-4-1-20250805                                                               |
    | **Claude API alias**                                                  | claude-opus-4-7                                                                                                      | claude-opus-4-6                                                                      | claude-sonnet-4-6                                                                    | claude-sonnet-4-5                                                                      | claude-opus-4-5                                                                        | claude-opus-4-1                                                                        |
    | **AWS Bedrock ID**                                                    | anthropic.claude-opus-4-76                                                                                           | anthropic.claude-opus-4-6-v1                                                         | anthropic.claude-sonnet-4-6                                                          | anthropic.claude-sonnet-4-5-20250929-v1:0                                              | anthropic.claude-opus-4-5-20251101-v1:0                                                | anthropic.claude-opus-4-1-20250805-v1:0                                                |
    | **Google Cloud ID**                                                   | claude-opus-4-7                                                                                                      | claude-opus-4-6                                                                      | claude-sonnet-4-6                                                                    | claude-sonnet-4-5\@20250929                                                            | claude-opus-4-5\@20251101                                                              | claude-opus-4-1\@20250805                                                              |
    | **Pricing**                                                           | $5 / input MTok $25 / output MTok                                                                                    | $5 / input MTok $25 / output MTok                                                    | $3 / input MTok $15 / output MTok                                                    | $3 / input MTok $15 / output MTok                                                      | $5 / input MTok $25 / output MTok                                                      | $15 / input MTok $75 / output MTok                                                     |
    | **[Extended thinking](/docs/en/build-with-claude/extended-thinking)** | No                                                                                                                   | Yes                                                                                  | Yes                                                                                  | Yes                                                                                    | Yes                                                                                    | Yes                                                                                    |
    | **[Adaptive thinking](/docs/en/build-with-claude/adaptive-thinking)** | Yes                                                                                                                  | Yes                                                                                  | Yes                                                                                  | No                                                                                     | No                                                                                     | No                                                                                     |
    | **Comparative latency**                                               | Moderate                                                                                                             | Moderate                                                                             | Fast                                                                                 | Fast                                                                                   | Moderate                                                                               | Moderate                                                                               |
    | **Context window**                                                    | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters (Opus 4.7 uses a new tokenizer)">1M tokens</Tooltip> | <Tooltip tooltipContent="~750k words \ ~3.4M unicode characters">1M tokens</Tooltip> | <Tooltip tooltipContent="~750k words \ ~3.4M unicode characters">1M tokens</Tooltip> | <Tooltip tooltipContent="~150k words \ ~680k unicode characters">200k tokens</Tooltip> | <Tooltip tooltipContent="~150k words \ ~680k unicode characters">200k tokens</Tooltip> | <Tooltip tooltipContent="~150k words \ ~680k unicode characters">200k tokens</Tooltip> |
    | **Max output**                                                        | 128k tokens                                                                                                          | 128k tokens                                                                          | 128k tokens                                                                          | 64k tokens                                                                             | 64k tokens                                                                             | 32k tokens                                                                             |
    | **Reliable knowledge cutoff**                                         | Jan 20265                                                                                                            | May 20255                                                                            | Aug 20255                                                                            | Jan 20255                                                                              | May 20255                                                                              | Jan 20255                                                                              |
    | **Training data cutoff**                                              | Jan 2026                                                                                                             | Aug 2025                                                                             | Jan 2026                                                                             | Jul 2025                                                                               | Aug 2025                                                                               | Mar 2025                                                                               |

    <Warning>
      Claude Opus 4.1 (`claude-opus-4-1-20250805`) is deprecated and will be retired on August 5, 2026. Migrate to [Claude Opus 4.8](/docs/en/about-claude/models/migration-guide#migrating-from-claude-opus-47) before the retirement date.

      See [model deprecations](/docs/en/about-claude/model-deprecations) for details.
    </Warning>

    *5 - **Reliable knowledge cutoff** indicates the date through which a model's knowledge is most extensive and reliable. **Training data cutoff** is the broader date range of training data used.*

    *6 - Claude Opus 4.7 is available on Bedrock through [Claude in Amazon Bedrock](/docs/en/build-with-claude/claude-in-amazon-bedrock) (the Messages-API Bedrock endpoint).*
  </Accordion>
</AccordionGroup>
  - now: You can query model capabilities and token limits programmatically with the [Models API](https://platform.claude.com/docs/en/api/models/list). The response includes `max_input_tokens`, `max_tokens`, and a `capabilities` object for every available model.
- **reprojection** — same-statement update (similarity >= threshold)
  - was: Claude 4 models excel in:
  - now: Current Claude models excel in:
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: * **Performance:** Top-tier results in reasoning, coding, multilingual tasks, long-context handling, honesty, and image processing. See the [Claude 4 blog post](https://www.anthropic.com/news/claude-4) for more information.

* **Engaging responses:** Claude models are ideal for applications that require rich, human-like interactions.

  * If you prefer more concise responses, you can adjust your prompts to guide the model toward the desired output length. Refer to the [prompt engineering guides](/docs/en/build-with-claude/prompt-engineering) for details.
  * For prompting best practices, see [Prompting best practices](/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).

* **Output quality:** When migrating from previous model generations to Claude 4, you may notice larger improvements in overall performance.

## Migrating to Claude Opus 4.8

If you're currently using Claude Opus 4.7 or earlier Claude models, see [Migrating to Claude Opus 4.8](/docs/en/about-claude/models/migration-guide#migrating-from-claude-opus-47).

## Migrating to Claude Opus 4.7

If you're currently using Claude Opus 4.6 or older Claude models, see [Migrating to Claude Opus 4.7](/docs/en/about-claude/models/migration-guide#migrating-to-claude-opus-4-7).
  - now: * **Performance:** Top-tier results in reasoning, coding, multilingual tasks, long-context handling, honesty, and image processing. See [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) for general and model-specific prompting guidance.
* **Engaging responses:** Claude models are ideal for applications that require rich, human-like interactions. If you prefer more concise responses, adjust your prompts to guide the model toward the desired output length. Refer to the [prompt engineering guides](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering) for details.
* **Output quality:** When migrating from a previous model generation, you may notice larger improvements in overall performance. If you're on Claude Opus 4.8 or earlier, see [Migrating to Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/migration-guide).
- **removal** — removes a previously-present capability claim
  - was: <Note>
  Looking to chat with Claude? Visit

  [claude.ai](https://claude.ai)

  !
</Note>
- **reprojection** — same-statement update (similarity >= threshold)
  - was: <Card title="Intro to Claude" icon="check" href="/docs/en/intro">
  - now: <Card title="Intro to Claude" icon="check" href="https://platform.claude.com/docs/en/intro">
- **reprojection** — same-statement update (similarity >= threshold)
  - was: <Card title="Quickstart" icon="lightning" href="/docs/en/get-started">
  - now: <Card title="Quickstart" icon="lightning" href="https://platform.claude.com/docs/en/get-started">
- **contradiction-suspect** — replacement text is not a rewording of the old (similarity < threshold); may contradict it
  - was: <Card title="Claude Console" icon="code" href="/">
    Craft and test powerful prompts directly in your browser.
  - now: <Card title="Choosing a model" icon="compass" href="https://platform.claude.com/docs/en/about-claude/models/choosing-a-model">
    Establish criteria and pick the right model for your use case.
  </Card>

  <Card title="Pricing" icon="coins" href="https://platform.claude.com/docs/en/about-claude/pricing">
    Complete pricing, including batch discounts and prompt caching rates.
  </Card>

  <Card title="Model deprecations" icon="clock" href="https://platform.claude.com/docs/en/about-claude/model-deprecations">
    Lifecycle status and retirement commitments for every model.
  </Card>

  <Card title="Claude Console" icon="code" href="https://platform.claude.com/">
    Craft and test prompts directly in your browser.
- **reprojection** — same-statement update (similarity >= threshold)
  - was: If you have any questions or need assistance, don't hesitate to reach out to the [support team](https://support.claude.com/) or consult the [Discord community](https://www.anthropic.com/discord).
  - now: Looking to chat with Claude? Visit [claude.ai](https://claude.ai). If you have questions, reach out to the [support team](https://support.claude.com/) or the [Discord community](https://www.anthropic.com/discord).
