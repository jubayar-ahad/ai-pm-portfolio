"""Bounded multi-step agent loop for the tool-use-agent.

Slice 3 shipped the bounded loop; slice 4 canonicalizes the refusal
surface. The loop now exits in one of three deterministic states, all
of which write to ``AgentResult.refusal_reason`` so the future evals
harness can bucket them without parsing ``final_text``:

* ``stop_reason="end_turn"`` — the model emitted no ``tool_use`` blocks
  and the loop returns its text as ``final_text``. When that text is
  byte-equal to ``REFUSAL_SENTENCE`` per system-prompt rule 1,
  ``refusal_reason="model_refused"`` is set so the harness can group
  it with the other refusal paths.
* ``stop_reason="repeated_tool_error"`` — the same ``(tool, input)``
  pair errored in two consecutive steps. The loop terminates with
  ``final_text=REFUSAL_SENTENCE`` and
  ``refusal_reason="repeated_tool_error"`` rather than letting the
  model spin on a broken call.
* ``stop_reason="max_steps_exhausted"`` — the bounded loop hit
  ``--max-steps`` without an ``end_turn``. ``final_text`` is now the
  canonical ``REFUSAL_SENTENCE`` (replacing the slice-3 placeholder
  cap note), with ``refusal_reason="max_steps_exhausted"``.

The dry-run path returns the assembled first-turn prompt and the
configured ``max_steps`` cap, without importing the SDK. This is the
same property the ``rag-app/`` build holds: the CLI is verifiable
without an API key.

Cross-build refusal alignment: ``REFUSAL_SENTENCE`` is defined exactly
once in ``tool_use_agent/verify.py`` and byte-identical with
``rag-app/rag_app/verify.py``. The future evals harness asserts the
two are equal at startup.
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
from tool_use_agent.verify import (
    REFUSAL_SENTENCE,
    canonical_call_key,
    detect_repeated_error,
    is_model_refusal,
)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_MAX_STEPS = 6

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
    refusal_reason: str | None = None
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
    prev_step_error_keys: set[str] = set()

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

        if not tool_use_blocks:
            # Model decided it has enough — emit final answer. Steps taken
            # is the count of tool rounds actually executed (0 if the model
            # answered directly on turn 1).
            final_text = "".join(text_parts).strip()
            result.final_text = final_text
            result.steps_taken = step_num - 1
            if is_model_refusal(final_text):
                result.refusal_reason = "model_refused"
            return result

        # Execute every tool the model requested in this turn. Recoverable
        # errors surface as tool_result.is_error=true so the model can
        # react; we additionally track the canonical (tool, input) keys
        # that errored this step so we can refuse if the model retries
        # the same broken call on the next step.
        tool_result_blocks: list[dict[str, Any]] = []
        this_step_error_keys: set[str] = set()
        for tu in tool_use_blocks:
            tool_name = tu.name
            tool_input = dict(tu.input)
            is_error = False
            try:
                output = call_tool(tool_name, repo_root, **tool_input)
            except (KeyError, TypeError, ValueError) as err:
                output = f"ERROR: {type(err).__name__}: {err}"
                is_error = True
            if is_error:
                this_step_error_keys.add(
                    canonical_call_key(tool_name, tool_input)
                )
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

        result.steps_taken = step_num

        # Refusal trigger: same (tool, input) errored in two consecutive
        # steps. Terminate with the canonical refusal rather than
        # appending another tool_result turn the model would just retry.
        repeated = detect_repeated_error(
            prev_step_error_keys, this_step_error_keys
        )
        if repeated is not None:
            result.stop_reason = "repeated_tool_error"
            result.refusal_reason = "repeated_tool_error"
            result.final_text = REFUSAL_SENTENCE
            return result

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_result_blocks})
        prev_step_error_keys = this_step_error_keys

    # Loop exhausted before the model returned end_turn. Emit the
    # canonical REFUSAL_SENTENCE so the evals harness can bucket the
    # max_steps_exhausted path with other refusals via a single
    # equality check.
    result.stop_reason = "max_steps_exhausted"
    result.refusal_reason = "max_steps_exhausted"
    result.final_text = REFUSAL_SENTENCE
    return result
