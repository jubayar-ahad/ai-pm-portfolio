"""Tests for tool_use_agent.agent: dry-run + bounded loop + 4-bucket refusal.

The Anthropic SDK is stubbed by injecting a fake ``anthropic`` module into
``sys.modules`` before ``run_agent`` does its lazy import. That keeps tests
key-free and offline while exercising the real loop body.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pytest

from tool_use_agent.agent import (
    DEFAULT_MAX_STEPS,
    DEFAULT_MODEL,
    AgentResult,
    SYSTEM_PROMPT,
    ToolCallTrace,
    build_dry_run_result,
    build_user_message,
    run_agent,
)
from tool_use_agent.verify import REFUSAL_SENTENCE


# ----- Stub Anthropic SDK ----------------------------------------------------


@dataclass
class StubBlock:
    type: str
    text: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)
    id: str = "tu_stub"


@dataclass
class StubUsage:
    input_tokens: int = 5
    output_tokens: int = 7


@dataclass
class StubResponse:
    content: list = field(default_factory=list)
    stop_reason: str = "end_turn"
    model: str = "claude-haiku-4-5-stub"
    usage: StubUsage = field(default_factory=StubUsage)


class StubMessages:
    def __init__(self, responses: list[StubResponse]):
        self.queue = list(responses)
        self.create_calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> StubResponse:
        self.create_calls.append(kwargs)
        # If the queue runs dry, repeat the final response — keeps the
        # max-steps-exhausted test simple.
        if len(self.queue) > 1:
            return self.queue.pop(0)
        return self.queue[0]


class StubAnthropic:
    def __init__(self, *args: Any, **kwargs: Any):
        self.messages = StubAnthropic._messages  # type: ignore[attr-defined]


def _install_stub_anthropic(monkeypatch, messages: StubMessages) -> None:
    """Inject a fake ``anthropic`` module that vends ``StubAnthropic``."""
    StubAnthropic._messages = messages  # type: ignore[attr-defined]
    fake_module = types.SimpleNamespace(Anthropic=StubAnthropic)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)


# ----- Pure helpers ----------------------------------------------------------


def test_build_user_message_format():
    assert build_user_message("What is X?") == "Question: What is X?"


def test_build_dry_run_result_populates_fields():
    result = build_dry_run_result("Q", max_steps=4)
    assert result.mode == "dry-run"
    assert result.question == "Q"
    assert result.max_steps == 4
    assert result.system_prompt == SYSTEM_PROMPT
    assert result.user_message == "Question: Q"
    assert result.tool_calls == []


def test_build_dry_run_result_default_max_steps():
    result = build_dry_run_result("Q")
    assert result.max_steps == DEFAULT_MAX_STEPS


def test_run_agent_rejects_zero_or_negative_max_steps(tiny_repo_root: Path):
    with pytest.raises(ValueError):
        run_agent("Q", repo_root=tiny_repo_root, max_steps=0)
    with pytest.raises(ValueError):
        run_agent("Q", repo_root=tiny_repo_root, max_steps=-1)


# ----- Refusal bucket 1: model emits REFUSAL_SENTENCE on end_turn ------------


def test_run_agent_model_refused_path(tiny_repo_root: Path, monkeypatch):
    responses = [
        StubResponse(
            content=[StubBlock(type="text", text=REFUSAL_SENTENCE)],
            stop_reason="end_turn",
        )
    ]
    messages = StubMessages(responses)
    _install_stub_anthropic(monkeypatch, messages)
    result = run_agent("Q?", repo_root=tiny_repo_root)
    assert result.mode == "live"
    assert result.final_text == REFUSAL_SENTENCE
    assert result.refusal_reason == "model_refused"
    assert result.stop_reason == "end_turn"
    assert result.steps_taken == 0
    assert result.tool_calls == []


# ----- Refusal bucket 2: end_turn with a real answer -------------------------


def test_run_agent_end_turn_with_real_answer_no_refusal(
    tiny_repo_root: Path, monkeypatch
):
    responses = [
        StubResponse(
            content=[StubBlock(type="text", text="Pangolins are mammals.")],
            stop_reason="end_turn",
        )
    ]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root)
    assert result.final_text == "Pangolins are mammals."
    assert result.refusal_reason is None
    assert result.stop_reason == "end_turn"
    assert result.steps_taken == 0


# ----- Refusal bucket 3: max_steps_exhausted ---------------------------------


def test_run_agent_max_steps_exhausted_path(tiny_repo_root: Path, monkeypatch):
    """Model keeps requesting a successful tool call across all steps without
    ever emitting end_turn → cap fires with the canonical refusal text."""
    tool_block = StubBlock(
        type="tool_use",
        name="list_repo_files",
        input={"pattern": "*.md"},
        id="tu_1",
    )
    responses = [
        StubResponse(content=[tool_block], stop_reason="tool_use")
        for _ in range(3)
    ]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root, max_steps=3)
    assert result.refusal_reason == "max_steps_exhausted"
    assert result.stop_reason == "max_steps_exhausted"
    assert result.final_text == REFUSAL_SENTENCE
    assert result.steps_taken == 3
    assert len(result.tool_calls) == 3


# ----- Refusal bucket 4: repeated_tool_error ---------------------------------


def test_run_agent_repeated_tool_error_path(tiny_repo_root: Path, monkeypatch):
    """Same (tool, input) raises in two consecutive steps → refuse."""
    bad_block = StubBlock(
        type="tool_use",
        name="nonexistent_tool",
        input={"foo": "bar"},
        id="tu_err",
    )
    responses = [
        StubResponse(content=[bad_block], stop_reason="tool_use"),
        StubResponse(content=[bad_block], stop_reason="tool_use"),
    ]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root, max_steps=5)
    assert result.refusal_reason == "repeated_tool_error"
    assert result.stop_reason == "repeated_tool_error"
    assert result.final_text == REFUSAL_SENTENCE
    # Loop should exit at step 2, not run to max_steps.
    assert result.steps_taken == 2


# ----- Trace + step accounting ----------------------------------------------


def test_run_agent_tool_call_trace_fields(tiny_repo_root: Path, monkeypatch):
    tool_block = StubBlock(
        type="tool_use",
        name="grep_repo",
        input={"query": "Pangolin"},
        id="tu_1",
    )
    final_block = StubBlock(type="text", text="Found pangolins.")
    responses = [
        StubResponse(content=[tool_block], stop_reason="tool_use"),
        StubResponse(content=[final_block], stop_reason="end_turn"),
    ]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root)
    assert len(result.tool_calls) == 1
    call = result.tool_calls[0]
    assert isinstance(call, ToolCallTrace)
    assert call.tool == "grep_repo"
    assert call.input == {"query": "Pangolin"}
    assert call.is_error is False
    assert call.step == 1
    assert call.latency_ms >= 0
    assert call.output_len > 0
    assert result.steps_taken == 1
    assert result.refusal_reason is None


def test_run_agent_parallel_tool_calls_share_step_number(
    tiny_repo_root: Path, monkeypatch
):
    tool_a = StubBlock(
        type="tool_use", name="list_repo_files", input={}, id="tu_a"
    )
    tool_b = StubBlock(
        type="tool_use", name="count_by_bucket", input={}, id="tu_b"
    )
    final = StubBlock(type="text", text="Done.")
    responses = [
        StubResponse(content=[tool_a, tool_b], stop_reason="tool_use"),
        StubResponse(content=[final], stop_reason="end_turn"),
    ]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root)
    assert len(result.tool_calls) == 2
    assert {c.step for c in result.tool_calls} == {1}


def test_run_agent_tracks_token_usage(tiny_repo_root: Path, monkeypatch):
    final = StubBlock(type="text", text="Hello.")
    responses = [StubResponse(content=[final], stop_reason="end_turn",
                              usage=StubUsage(input_tokens=11, output_tokens=22))]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root)
    assert result.input_tokens == 11
    assert result.output_tokens == 22
    assert result.model == "claude-haiku-4-5-stub"


def test_run_agent_max_steps_override_honored(
    tiny_repo_root: Path, monkeypatch
):
    tool_block = StubBlock(
        type="tool_use", name="list_repo_files", input={}, id="tu_x"
    )
    responses = [
        StubResponse(content=[tool_block], stop_reason="tool_use")
        for _ in range(10)
    ]
    _install_stub_anthropic(monkeypatch, StubMessages(responses))
    result = run_agent("Q?", repo_root=tiny_repo_root, max_steps=2)
    assert result.max_steps == 2
    assert result.steps_taken == 2
    assert result.refusal_reason == "max_steps_exhausted"


def test_agentresult_dataclass_defaults():
    result = AgentResult(
        mode="dry-run",
        question="q",
        system_prompt="s",
        user_message="u",
    )
    assert result.max_steps == DEFAULT_MAX_STEPS
    assert result.steps_taken == 0
    assert result.tool_calls == []
    assert result.refusal_reason is None
    assert result.stop_reason is None
    assert result.input_tokens == 0
    assert result.output_tokens == 0


def test_default_model_is_haiku():
    # Sanity check on the published default — the agent loop's default
    # surfaces in the dry-run record.
    assert "claude" in DEFAULT_MODEL
