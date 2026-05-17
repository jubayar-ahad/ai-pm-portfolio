# Building with Extended Thinking

Extended thinking gives Claude enhanced reasoning capabilities for complex tasks, while providing varying levels of transparency into its step-by-step thought process before delivering its final answer.

## Key Updates for Current Models

**Claude Opus 4.7**: Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is no longer supported. Use adaptive thinking (`thinking: {type: "adaptive"}`) with the effort parameter instead.

**Claude Opus 4.6 & Claude Sonnet 4.6**: Adaptive thinking is recommended; manual mode is deprecated but still functional.

## How Extended Thinking Works

When enabled, Claude creates `thinking` content blocks containing its internal reasoning, then incorporates insights from this reasoning into its final response. The API response includes `thinking` blocks followed by `text` blocks:

```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me analyze this step by step...",
      "signature": "WaUjzkypQ2mUEVM36O2TxuC06KN8xyfbJwyem2dw3URve..."
    },
    {
      "type": "text",
      "text": "Based on my analysis..."
    }
  ]
}
```

## Basic Usage Example

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[
        {
            "role": "user",
            "content": "Are there an infinite number of prime numbers such that n mod 4 == 3?",
        }
    ],
)

for block in response.content:
    if block.type == "thinking":
        print(f"\nThinking summary: {block.thinking}")
    elif block.type == "text":
        print(f"\nResponse: {block.text}")
```

## Controlling Thinking Display

The `display` field controls how thinking is returned:

- **`"summarized"`** (default on Claude 4 models): Returns summarized thinking text.
- **`"omitted"`** (default on Opus 4.7 and Claude Mythos): Returns empty thinking field with signature only; faster streaming since thinking tokens aren't sent.

## Streaming with Thinking

When streaming, thinking content arrives via `thinking_delta` events. When `display: "omitted"` is set, no `thinking_delta` events are emitted — only the signature arrives, enabling faster time-to-first-text-token.

## Extended Thinking with Tool Use

Extended thinking works with tool use, but with important limitations:

- **Tool choice**: Only supports `tool_choice: {"type": "auto"}` (default) or `tool_choice: {"type": "none"}`; forced tool use is incompatible.
- **Preserving thinking blocks**: You must pass thinking blocks back to the API unmodified when providing tool results to maintain reasoning continuity.
- **Single thinking mode per turn**: Cannot toggle thinking on/off mid-turn during tool use loops.

## Interleaved Thinking

Claude Mythos Preview, Opus 4.7, and Opus 4.6 support interleaved thinking, which enables Claude to think between tool calls for more sophisticated reasoning.

Support matrix:

- **Claude Mythos Preview**: Automatic; no beta header needed
- **Claude Opus 4.7**: Automatic with adaptive thinking
- **Claude Opus 4.6**: Automatic with adaptive thinking (recommended)
- **Claude Sonnet 4.6**: Automatic with adaptive thinking (recommended)
- **Other Claude 4 models**: Add `interleaved-thinking-2025-05-14` beta header with manual thinking

## Extended Thinking with Prompt Caching

Important considerations:

- **System prompt caching**: Preserved when thinking parameters change; cache hits expected.
- **Messages caching**: Invalidated when thinking parameters change (budget allocation or enable/disable).
- **Thinking block context**: On Opus 4.5+ and Sonnet 4.6+, thinking blocks are kept by default. On earlier models, they're removed from context (but must still be passed in tool use loops).
- **Token counting**: Cached thinking blocks count as input tokens when read from cache.

### Billing Note

You're charged for full thinking tokens even with `display: "omitted"`. Omitting reduces latency, not cost. With summarized thinking, you're billed for the full thinking tokens, not just the summary.

## Important Notes

- **Zero Data Retention (ZDR)**: Extended thinking is eligible for ZDR; data isn't stored after API response.
- **Budget tokens**: Must be less than `max_tokens`; cannot be combined with `max_tokens: 0` (cache pre-warming).
- **Thinking model**: Summarization is processed by a different model that doesn't see the summarized output.
- **Rare cases**: Contact sales if you need access to full thinking output on Claude 4 models.
