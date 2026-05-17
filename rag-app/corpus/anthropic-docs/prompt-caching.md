# Prompt Caching

Prompt caching optimizes your API usage by allowing resuming from specific prefixes in your prompts. This significantly reduces processing time and costs for repetitive tasks or prompts with consistent elements.

This feature is eligible for Zero Data Retention (ZDR). When your organization has a ZDR arrangement, data sent through this feature is not stored after the API response is returned.

There are two ways to enable prompt caching:

- **Automatic caching**: Add a single `cache_control` field at the top level of your request. The system automatically applies the cache breakpoint to the last cacheable block and moves it forward as conversations grow. Best for multi-turn conversations where the growing message history should be cached automatically.
- **Explicit cache breakpoints**: Place `cache_control` directly on individual content blocks for fine-grained control over exactly what gets cached.

## How prompt caching works

When you send a request with prompt caching enabled:

1. The system checks if a prompt prefix, up to a specified cache breakpoint, is already cached from a recent query.
2. If found, it uses the cached version, reducing processing time and costs.
3. Otherwise, it processes the full prompt and caches the prefix once the response begins.

This is especially useful for:

- Prompts with many examples
- Large amounts of context or background information
- Repetitive tasks with consistent instructions
- Long multi-turn conversations

By default, the cache has a 5-minute lifetime. The cache is refreshed for no additional cost each time the cached content is used.

If you find that 5 minutes is too short, Anthropic also offers a 1-hour cache duration at additional cost.

Prompt caching references the entire prompt — `tools`, `system`, and `messages` (in that order) up to and including the block designated with `cache_control`.

## Pricing

Prompt caching introduces a new pricing structure. The table below shows the price per million tokens for each supported model:

| Model | Base Input Tokens | 5m Cache Writes | 1h Cache Writes | Cache Hits & Refreshes | Output Tokens |
|---|---|---|---|---|---|
| Claude Opus 4.7 | $5 / MTok | $6.25 / MTok | $10 / MTok | $0.50 / MTok | $25 / MTok |
| Claude Opus 4.6 | $5 / MTok | $6.25 / MTok | $10 / MTok | $0.50 / MTok | $25 / MTok |
| Claude Sonnet 4.6 | $3 / MTok | $3.75 / MTok | $6 / MTok | $0.30 / MTok | $15 / MTok |
| Claude Haiku 4.5 | $1 / MTok | $1.25 / MTok | $2 / MTok | $0.10 / MTok | $5 / MTok |

The table reflects the following pricing multipliers for prompt caching: 5-minute cache write tokens are 1.25 times the base input tokens price; 1-hour cache write tokens are 2 times the base input tokens price; cache read tokens are 0.1 times the base input tokens price.

## Automatic caching

Automatic caching is the simplest way to enable prompt caching. Instead of placing `cache_control` on individual content blocks, add a single `cache_control` field at the top level of your request body. The system automatically applies the cache breakpoint to the last cacheable block.

With automatic caching, the cache point moves forward automatically as conversations grow. Each new request caches everything up to the last cacheable block, and previous content is read from cache. The cache breakpoint automatically moves to the last cacheable block in each request, so you don't need to update any `cache_control` markers as the conversation grows.

By default, automatic caching uses a 5-minute TTL. You can specify a 1-hour TTL at 2x the base input token price.

Automatic caching is available on the Claude API, Claude Platform on AWS, and Microsoft Foundry (beta). Bedrock and Vertex AI do not support automatic caching.

## Explicit cache breakpoints

For more control over caching, you can place `cache_control` directly on individual content blocks. This is useful when you need to cache different sections that change at different frequencies, or need fine-grained control over exactly what gets cached.

Cache prefixes are created in the following order: `tools`, `system`, then `messages`. This order forms a hierarchy where each level builds upon the previous ones.

### How automatic prefix checking works

You can use just one cache breakpoint at the end of your static content, and the system will automatically find the longest prefix that a prior request already wrote to the cache.

Three core principles:

1. **Cache writes happen only at your breakpoint.** Marking a block with `cache_control` writes exactly one cache entry: a hash of the prefix ending at that block. The system does not write entries for any earlier position.
2. **Cache reads look backward for entries that prior requests wrote.** On each request the system computes the prefix hash at your breakpoint and checks for a matching cache entry. If none exists, it walks backward one block at a time, checking whether the prefix hash at each earlier position matches something already in the cache.
3. **The lookback window is 20 blocks.** The system checks at most 20 positions per breakpoint, counting the breakpoint itself as the first. If the system finds no matching entry in that window, checking stops.

**Common mistake: Breakpoint on content that changes every request.** Your prompt has a large static system context followed by a per-request block containing a timestamp and the user message. If you set `cache_control` on the per-request block, the timestamp differs each request, so the prefix hash at that block differs, and there is no cache hit. Move `cache_control` to the last block that stays the same across requests.

You can define up to 4 cache breakpoints if you want to cache different sections that change at different frequencies, have more control over exactly what gets cached, or ensure a cache hit when a growing conversation pushes your breakpoint 20 or more blocks past the last cache write.

## Caching strategies and considerations

### Cache limitations

The minimum cacheable prompt length is:

- 4,096 tokens for Claude Mythos Preview, Claude Opus 4.7, Claude Opus 4.6, and Claude Opus 4.5
- 1,024 tokens for Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.1, and deprecated Claude Opus 4
- 4,096 tokens for Claude Haiku 4.5

Shorter prompts cannot be cached, even if marked with `cache_control`. To verify whether a prompt was cached, check the response usage fields: if both `cache_creation_input_tokens` and `cache_read_input_tokens` are 0, the prompt was not cached.

Currently, "ephemeral" is the only supported cache type, which by default has a 5-minute lifetime.

### What can be cached

Most blocks in the request can be cached. This includes tools, system messages, text messages, images and documents, and tool use and tool results.

### What cannot be cached

- Thinking blocks cannot be cached directly with `cache_control`. However, thinking blocks CAN be cached alongside other content when they appear in previous assistant turns.
- Sub-content blocks (like citations) themselves cannot be cached directly. Instead, cache the top-level block.
- Empty text blocks cannot be cached.

### What invalidates the cache

The cache follows the hierarchy: `tools` → `system` → `messages`. Changes at each level invalidate that level and all subsequent levels. Modifying tool definitions invalidates the entire cache. Enabling/disabling web search or citations invalidates system and message caches. Changes to `tool_choice` only affect message blocks. Adding/removing images affects message blocks. Changes to extended thinking settings affect message blocks.

### Tracking cache performance

Monitor cache performance using these API response fields, within `usage` in the response (or `message_start` event if streaming):

- `cache_creation_input_tokens`: Number of tokens written to the cache when creating a new entry.
- `cache_read_input_tokens`: Number of tokens retrieved from the cache for this request.
- `input_tokens`: Number of input tokens which were not read from or used to create a cache.

To calculate total input tokens: `total_input_tokens = cache_read_input_tokens + cache_creation_input_tokens + input_tokens`.

### Best practices for effective caching

- Start with automatic caching for multi-turn conversations.
- Use explicit block-level breakpoints when you need to cache different sections with different change frequencies.
- Cache stable, reusable content like system instructions, background information, large contexts, or frequent tool definitions.
- Place cached content at the prompt's beginning for best performance.
- Place the breakpoint on the last block that stays identical across requests.
- Regularly analyze cache hit rates and adjust your strategy as needed.

## 1-hour cache duration

If you find that 5 minutes is too short, Anthropic also offers a 1-hour cache duration at additional cost. To use the extended cache, include `ttl` in the `cache_control` definition:

```json
{ "cache_control": { "type": "ephemeral", "ttl": "1h" } }
```

The 1-hour cache is best used when prompts are used less frequently than 5 minutes but more frequently than every hour, when latency is important and your follow-up prompts may be sent beyond 5 minutes, or when you want to improve your rate limit utilization since cache hits are not deducted against your rate limit.

## Pre-warming the cache

Cache pre-warming lets you load your system prompt or tool definitions into the prompt cache before a user triggers a real request. This eliminates the cache-miss latency penalty on the first user interaction, reducing time-to-first-token (TTFT) for latency-sensitive applications.

Set `max_tokens: 0` in your request. The API runs the full prefill phase (reading your prompt into the model and writing the cache at any `cache_control` breakpoint), then returns immediately without generating any output. The response has an empty `content` array, `stop_reason: "max_tokens"`, and a fully populated `usage` block.

Place the `cache_control` breakpoint on the last block that is shared with the follow-up request (typically your system prompt or tool definitions), not on the placeholder user message. A pre-warm request incurs a **cache write** charge if the prefix is not already cached, the same as any other request. Zero output tokens are billed.
