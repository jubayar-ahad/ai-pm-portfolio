"""Single-step agent loop for the tool-use-agent.

Slice 2: one Claude turn with ``tools=[…]``, execute whichever tool the
model requests, return the result, then get the model's final answer.
No multi-step chaining yet — that lands in slice 3 by lifting the
``SINGLE_STEP_MAX_STEPS`` cap into a bounded loop.

The dry-run path returns the assembled prompt and the catalog the model
would see, without importing the SDK. This is the same property the
``rag-app/`` build holds: the CLI is verifiable without an API key.

Cross-build refusal alignment: ``REFUSAL_SENTENCE`` is defined with the
same literal string as ``rag-app/rag_app/verify.py`` so the future
evals harness can bucket refusals from both builds without fuzzy match.
Slice 4 will centralize and enforce the refusal path mechanically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tool_use_agent.catalog import (
    call_tool,
    catalog_as_anthropic_tools,
)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 1024

# Slice 2 caps at one tool-call cycle; slice 3 will lift this to a real
# bounded loop with `max_steps=6` per the README stack table.
SINGLE_STEP_MAX_STEPS = 1

REFUSAL_SENTENCE = (
    "I don't have enough information in the provided context to answer this."
)

SYSTEM_PROMPT = f"""\
You are a careful question-answering assistant for the AI PM 90-day project repo.

You have access to a small set of read-only tools that let you enumerate, read,
and search files in this repo, and inspect the interview-pipeline tracker. To
answer a question, decide which tool to call (if any), call it, and ground
your answer in the tool result.

Rules, in order of priority:

1. If no tool can produce evidence that supports an answer, reply exactly with
   this sentence and nothing else:
   "{REFUSAL_SENTENCE}"

2. Prefer the smallest, most targeted tool call. Read a specific line range
   rather than a whole file when you can; filter the pipeline tracker by
   stage or bucket rather than listing everything.

3. Be concise. Quote brief snippets from tool results when helpful, but do
   not paste long file contents back to the user.

4. Tool results are the only evidence available to you. Do not draw on
   outside knowledge or claims the tool results do not support.
"""


@dataclass(frozen=True)
class ToolCallTrace:
    """One executed tool call inside the agent loop, JSON-friendly."""

    tool: str
    input: dict[str, Any]
    output: Any
    is_error: bool = False


@dataclass
class AgentResult:
    """Everything produced by one `ask` invocation, dry-run or live."""

    mode: str  # "live" or "dry-run"
    question: str
    system_prompt: str
    user_message: str
    tool_calls: list[ToolCallTrace] = field(default_factory=list)
    final_text: str = ""
    stop_reason: str | None = None
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


def build_user_message(question: str) -> str:
    """Pure: assemble the first-turn user message for a question."""
    return f"Question: {question}"


def build_dry_run_result(question: str) -> AgentResult:
    """Assemble the prompt the live path would send, no SDK import."""
    return AgentResult(
        mode="dry-run",
        question=question,
        system_prompt=SYSTEM_PROMPT,
        user_message=build_user_message(question),
    )


def run_single_step(
    question: str,
    repo_root: Path,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> AgentResult:
    """Single-step agent loop: one tool-call cycle, then a final answer.

    The Anthropic SDK is imported lazily so a fresh checkout without
    ``pip install`` still runs ``catalog``, ``tool``, and ``ask --dry-run``.
    """
    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover - install-time error
        raise RuntimeError(
            "The 'anthropic' package is required for live agent runs. "
            "Install it with `pip install -r tool-use-agent/requirements.txt`, "
            "or re-run with --dry-run to inspect the prompt without "
            "calling the model."
        ) from exc

    client = Anthropic()
    tools = catalog_as_anthropic_tools()
    user_message = build_user_message(question)
    result = AgentResult(
        mode="live",
        question=question,
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
    )

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_message},
    ]

    # Turn 1: send the question. The model may answer directly or emit one
    # or more tool_use blocks asking us to run something.
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
    )
    result.model = response.model
    result.input_tokens += response.usage.input_tokens
    result.output_tokens += response.usage.output_tokens
    result.stop_reason = response.stop_reason

    text_parts: list[str] = []
    tool_use_blocks: list[Any] = []
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_parts.append(block.text)
        elif block_type == "tool_use":
            tool_use_blocks.append(block)

    if not tool_use_blocks:
        result.final_text = "".join(text_parts).strip()
        return result

    # Execute every tool the model requested in turn 1.
    tool_result_blocks: list[dict[str, Any]] = []
    for tu in tool_use_blocks:
        tool_name = tu.name
        tool_input = dict(tu.input)
        is_error = False
        try:
            output = call_tool(tool_name, repo_root, **tool_input)
        except (KeyError, TypeError, ValueError) as err:
            # Recoverable errors (unknown tool name, bad kwargs, bad value)
            # become structured tool_result.is_error=True content so the
            # model can react. Slice 4 will add policy on top of this.
            output = f"ERROR: {type(err).__name__}: {err}"
            is_error = True
        result.tool_calls.append(
            ToolCallTrace(
                tool=tool_name,
                input=tool_input,
                output=output,
                is_error=is_error,
            )
        )
        tool_result_blocks.append(
            {
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(output, ensure_ascii=False, default=str),
                "is_error": is_error,
            }
        )

    # Turn 2: echo the assistant's content back, send tool results, get the
    # final answer. Any further tool_use blocks here are deferred to slice 3.
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_result_blocks})

    response2 = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
    )
    result.input_tokens += response2.usage.input_tokens
    result.output_tokens += response2.usage.output_tokens
    result.stop_reason = response2.stop_reason

    text_parts2: list[str] = []
    deferred_tool_uses: list[Any] = []
    for block in response2.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_parts2.append(block.text)
        elif block_type == "tool_use":
            deferred_tool_uses.append(block)

    final_text = "".join(text_parts2).strip()
    if deferred_tool_uses:
        # Surface the slice-2 cap rather than silently dropping the request.
        result.stop_reason = "single_step_cap_reached"
        deferred_names = ", ".join(t.name for t in deferred_tool_uses)
        cap_note = (
            f"(stopped after one tool-call cycle; model wanted to call: "
            f"{deferred_names}. Multi-step chaining lands in slice 3.)"
        )
        result.final_text = (
            f"{final_text}\n\n{cap_note}" if final_text else cap_note
        )
    else:
        result.final_text = final_text

    return result
