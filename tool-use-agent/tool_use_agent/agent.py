"""Bounded multi-step agent loop for the tool-use-agent.

Slice 3: run the model with ``tools=[…]`` in a bounded loop, executing
whichever tool(s) the model requests each turn, until the model returns
``end_turn`` without a new ``tool_use`` block or ``max_steps`` is reached.

Each "step" is one round of (model call → tool execution). ``max_steps``
caps the number of tool-execution rounds and is the only knob a caller
needs for cost-bounding. A model turn that emits no ``tool_use`` blocks
terminates the loop with ``stop_reason=end_turn`` and the model's text
as ``final_text``. Reaching the cap exits with
``stop_reason=max_steps_exhausted`` and a deterministic cap note as
``final_text`` — slice 4 will swap that for the canonical refusal
sentence.

The dry-run path returns the assembled first-turn prompt and the
configured ``max_steps`` cap, without importing the SDK. This is the
same property the ``rag-app/`` build holds: the CLI is verifiable
without an API key.

Cross-build refusal alignment: ``REFUSAL_SENTENCE`` is defined with the
same literal string as ``rag-app/rag_app/verify.py`` so the future
evals harness can bucket refusals from both builds without fuzzy match.
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
DEFAULT_MAX_STEPS = 6

REFUSAL_SENTENCE = (
    "I don't have enough information in the provided context to answer this."
)

SYSTEM_PROMPT = f"""\
You are a careful question-answering assistant for the AI PM 90-day project repo.

You have access to a small set of read-only tools that let you enumerate, read,
and search files in this repo, and inspect the interview-pipeline tracker. To
answer a question, decide which tool to call (if any), call it, and ground
your answer in the tool result. You may chain tool calls across turns; each
turn you should either request the next tool or emit your final answer.

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
    """One executed tool call inside the agent loop, JSON-friendly.

    ``step`` is the 1-indexed bounded-loop round in which this call was
    issued. Multiple tool calls can share the same ``step`` when the
    model emits parallel ``tool_use`` blocks in a single turn.
    """

    tool: str
    input: dict[str, Any]
    output: Any
    is_error: bool = False
    step: int = 1


@dataclass
class AgentResult:
    """Everything produced by one `ask` invocation, dry-run or live."""

    mode: str  # "live" or "dry-run"
    question: str
    system_prompt: str
    user_message: str
    max_steps: int = DEFAULT_MAX_STEPS
    steps_taken: int = 0
    tool_calls: list[ToolCallTrace] = field(default_factory=list)
    final_text: str = ""
    stop_reason: str | None = None
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


def build_user_message(question: str) -> str:
    """Pure: assemble the first-turn user message for a question."""
    return f"Question: {question}"


def build_dry_run_result(
    question: str, max_steps: int = DEFAULT_MAX_STEPS
) -> AgentResult:
    """Assemble the prompt the live path would send, no SDK import."""
    return AgentResult(
        mode="dry-run",
        question=question,
        system_prompt=SYSTEM_PROMPT,
        user_message=build_user_message(question),
        max_steps=max_steps,
    )


def run_agent(
    question: str,
    repo_root: Path,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> AgentResult:
    """Bounded multi-step agent loop.

    The Anthropic SDK is imported lazily so a fresh checkout without
    ``pip install`` still runs ``catalog``, ``tool``, and ``ask --dry-run``.
    """
    if max_steps < 1:
        raise ValueError(f"max_steps must be >= 1 (got {max_steps})")

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
        max_steps=max_steps,
    )

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_message},
    ]
    last_text_parts: list[str] = []

    for step_num in range(1, max_steps + 1):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )
        if result.model is None:
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
        last_text_parts = text_parts

        if not tool_use_blocks:
            # Model decided it has enough — emit final answer. Steps taken
            # is the count of tool rounds actually executed (0 if the model
            # answered directly on turn 1).
            result.final_text = "".join(text_parts).strip()
            result.steps_taken = step_num - 1
            return result

        # Execute every tool the model requested in this turn. Errors
        # are surfaced as tool_result.is_error=true so the model can
        # recover on a subsequent step; slice 4 will add policy on top.
        tool_result_blocks: list[dict[str, Any]] = []
        for tu in tool_use_blocks:
            tool_name = tu.name
            tool_input = dict(tu.input)
            is_error = False
            try:
                output = call_tool(tool_name, repo_root, **tool_input)
            except (KeyError, TypeError, ValueError) as err:
                output = f"ERROR: {type(err).__name__}: {err}"
                is_error = True
            result.tool_calls.append(
                ToolCallTrace(
                    tool=tool_name,
                    input=tool_input,
                    output=output,
                    is_error=is_error,
                    step=step_num,
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

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_result_blocks})
        result.steps_taken = step_num

    # Loop exhausted before the model returned end_turn. Surface the cap
    # explicitly; slice 4 will replace this deterministic note with the
    # canonical REFUSAL_SENTENCE so the evals harness can bucket the
    # max_steps_exhausted path together with other refusals.
    result.stop_reason = "max_steps_exhausted"
    cap_note = (
        f"(reached max_steps={max_steps} without a grounded answer; "
        f"canonical refusal lands in slice 4.)"
    )
    closing_text = "".join(last_text_parts).strip()
    result.final_text = (
        f"{closing_text}\n\n{cap_note}" if closing_text else cap_note
    )
    return result
