# Models overview

Claude is a family of state-of-the-art large language models developed by Anthropic. This guide introduces the available models and compares their performance.

## Choosing a model

If you're unsure which model to use, consider starting with **Claude Opus 4.7** for the most complex tasks. It is our most capable generally available model, with a step-change improvement in agentic coding over Claude Opus 4.6.

All current Claude models support text and image input, text output, multilingual capabilities, and vision. Models are available through the Claude API, Claude Platform on AWS, Amazon Bedrock, Vertex AI, and Microsoft Foundry.

### Latest models comparison

| Feature | Claude Opus 4.7 | Claude Sonnet 4.6 | Claude Haiku 4.5 |
|:--------|:--------------|:------------------|:-----------------|
| Description | Our most capable generally available model for complex reasoning and agentic coding | The best combination of speed and intelligence | The fastest model with near-frontier intelligence |
| Claude API ID | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5-20251001 |
| Claude API alias | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5 |
| AWS Bedrock ID | anthropic.claude-opus-4-7 | anthropic.claude-sonnet-4-6 | anthropic.claude-haiku-4-5-20251001-v1:0 |
| Vertex AI ID | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5@20251001 |
| Pricing | $5 / input MTok, $25 / output MTok | $3 / input MTok, $15 / output MTok | $1 / input MTok, $5 / output MTok |
| Extended thinking | No | Yes | Yes |
| Adaptive thinking | Yes | Yes | No |
| Priority Tier | Yes | Yes | Yes |
| Comparative latency | Moderate | Fast | Fastest |
| Context window | 1M tokens | 1M tokens | 200k tokens |
| Max output | 128k tokens | 64k tokens | 64k tokens |
| Reliable knowledge cutoff | Jan 2026 | Aug 2025 | Feb 2025 |
| Training data cutoff | Jan 2026 | Jan 2026 | Jul 2025 |

**Reliable knowledge cutoff** indicates the date through which a model's knowledge is most extensive and reliable. **Training data cutoff** is the broader date range of training data used.

Claude Opus 4.7 is available on Bedrock through Claude in Amazon Bedrock (the Messages-API Bedrock endpoint).

Every Claude model ID is a pinned snapshot. Models with a date in the ID (for example, `20250929`) are fixed to that specific release. Starting with the Claude 4.6 generation, model IDs use a dateless format that is also a pinned snapshot, not an evergreen pointer. For models before the 4.6 generation, entries in the Claude API alias column are convenience pointers that resolve to a dated model ID.

Starting with **Claude Sonnet 4.5 and all subsequent models** (including Claude Sonnet 4.6), Bedrock offers two endpoint types: **global endpoints** (dynamic routing for maximum availability) and **regional endpoints** (guaranteed data routing through specific geographic regions). Vertex AI offers three endpoint types: global endpoints, **multi-region endpoints** (dynamic routing within a geographic area), and regional endpoints.

**Claude Platform on AWS** uses the same model IDs as the Claude API (for example, `claude-opus-4-6`), not Bedrock-style IDs. Model lifecycle on Claude Platform on AWS follows Anthropic's first-party Model deprecations, not Bedrock's.

You can query model capabilities and token limits programmatically with the Models API. The response includes `max_input_tokens`, `max_tokens`, and a `capabilities` object for every available model.

The Max output values above apply to the synchronous Messages API. On the Message Batches API, Opus 4.7, Opus 4.6, and Sonnet 4.6 support up to 300k output tokens by using the `output-300k-2026-03-24` beta header.

### Legacy models

The following models are still available. Consider migrating to current models for improved performance:

| Feature | Claude Opus 4.6 | Claude Sonnet 4.5 | Claude Opus 4.5 | Claude Opus 4.1 | Claude Sonnet 4 (deprecated) | Claude Opus 4 (deprecated) |
|:--------|:----------------|:------------------|:----------------|:----------------|:----------------|:--------------|
| Claude API ID | claude-opus-4-6 | claude-sonnet-4-5-20250929 | claude-opus-4-5-20251101 | claude-opus-4-1-20250805 | claude-sonnet-4-20250514 | claude-opus-4-20250514 |
| Pricing | $5 / $25 MTok | $3 / $15 MTok | $5 / $25 MTok | $15 / $75 MTok | $3 / $15 MTok | $15 / $75 MTok |
| Context window | 1M tokens | 200k tokens | 200k tokens | 200k tokens | 200k tokens | 200k tokens |
| Max output | 128k tokens | 64k tokens | 64k tokens | 32k tokens | 64k tokens | 32k tokens |

Claude Sonnet 4 (`claude-sonnet-4-20250514`) and Claude Opus 4 (`claude-opus-4-20250514`) are deprecated and will be retired on June 15, 2026. Migrate to Claude Sonnet 4.6 and Claude Opus 4.7 respectively before the retirement date.

## Prompt and output performance

Claude 4 models excel in:

- **Performance**: Top-tier results in reasoning, coding, multilingual tasks, long-context handling, honesty, and image processing.
- **Engaging responses**: Claude models are ideal for applications that require rich, human-like interactions. If you prefer more concise responses, you can adjust your prompts to guide the model toward the desired output length.
- **Output quality**: When migrating from previous model generations to Claude 4, you may notice larger improvements in overall performance.

## Migrating to Claude Opus 4.7

If you're currently using Claude Opus 4.6 or older Claude models, consider migrating to Claude Opus 4.7 to take advantage of improved intelligence and a step-change jump in agentic coding.

## Get started with Claude

If you're ready to start exploring what Claude can do for you, dive in. Whether you're a developer looking to integrate Claude into your applications or a user wanting to experience the power of AI firsthand, the docs provide quickstart guides, model overviews, and console workbench tools to help.
