"""Tests for tool_use_agent.verify: refusal sentence + repeated-error detector."""

from __future__ import annotations

from tool_use_agent.verify import (
    REFUSAL_SENTENCE,
    canonical_call_key,
    detect_repeated_error,
    is_model_refusal,
)


def test_refusal_sentence_is_locked_text():
    assert REFUSAL_SENTENCE == (
        "I don't have enough information in the provided context to answer this."
    )


def test_refusal_sentence_length_invariant():
    # 71 chars — the cross-build invariant first locked at iteration 9.
    assert len(REFUSAL_SENTENCE) == 71


def test_canonical_call_key_deterministic():
    a = canonical_call_key("grep_repo", {"query": "x", "max_matches": 5})
    b = canonical_call_key("grep_repo", {"query": "x", "max_matches": 5})
    assert a == b


def test_canonical_call_key_order_invariant():
    a = canonical_call_key("grep_repo", {"query": "x", "max_matches": 5})
    b = canonical_call_key("grep_repo", {"max_matches": 5, "query": "x"})
    assert a == b


def test_canonical_call_key_differs_when_input_differs():
    a = canonical_call_key("grep_repo", {"query": "x"})
    b = canonical_call_key("grep_repo", {"query": "y"})
    assert a != b


def test_canonical_call_key_differs_when_tool_differs():
    a = canonical_call_key("grep_repo", {"query": "x"})
    b = canonical_call_key("read_repo_file", {"query": "x"})
    assert a != b


def test_detect_repeated_error_returns_overlapping_key():
    k1 = canonical_call_key("grep_repo", {"query": "x"})
    k2 = canonical_call_key("read_repo_file", {"path": "y"})
    result = detect_repeated_error({k1, k2}, {k1})
    assert result == k1


def test_detect_repeated_error_returns_none_with_no_overlap():
    k1 = canonical_call_key("grep_repo", {"query": "x"})
    k2 = canonical_call_key("read_repo_file", {"path": "y"})
    assert detect_repeated_error({k1}, {k2}) is None


def test_detect_repeated_error_returns_none_for_empty_inputs():
    assert detect_repeated_error(set(), set()) is None
    k = canonical_call_key("grep_repo", {"query": "x"})
    assert detect_repeated_error({k}, set()) is None
    assert detect_repeated_error(set(), {k}) is None


def test_is_model_refusal_exact_match():
    assert is_model_refusal(REFUSAL_SENTENCE) is True


def test_is_model_refusal_strips_whitespace():
    assert is_model_refusal("  " + REFUSAL_SENTENCE + "\n") is True


def test_is_model_refusal_rejects_extra_prose():
    assert is_model_refusal("Sorry, " + REFUSAL_SENTENCE) is False
    assert is_model_refusal(REFUSAL_SENTENCE + " Try again.") is False


def test_is_model_refusal_rejects_empty_or_unrelated_text():
    assert is_model_refusal("") is False
    assert is_model_refusal("Pangolins are mammals.") is False


def test_refusal_sentence_byte_equal_to_rag_app():
    """Cross-build invariant: rag-app/verify.py and tool-use-agent/verify.py
    define the same canonical refusal string. Skipped if rag_app isn't
    importable from the test environment.
    """
    try:
        from rag_app.verify import REFUSAL_SENTENCE as RAG_REFUSAL
    except ImportError:
        import pytest

        pytest.skip("rag_app not importable from tool-use-agent test env")
    assert REFUSAL_SENTENCE == RAG_REFUSAL
