"""Tests for evals_harness.invariants: the two startup invariants.

Both invariants are run against the real sibling builds (rag_app and
tool_use_agent), which the harness adds to sys.path at import time.
Failure-injection tests use monkeypatch to mutate the imported constants
and confirm the InvariantError path fires.
"""

from __future__ import annotations

import sys

import pytest

from evals_harness import _repo
from evals_harness.invariants import (
    InvariantError,
    InvariantResult,
    _canonical_json_bytes,
    _short_digest,
    assert_refusal_sentence_equal,
    assert_trace_helpers_behavior,
    run_startup_invariants,
)


# Ensure sibling builds are on sys.path before importing them in tests.
_repo.ensure_build_imports_on_path()


def test_short_digest_is_16_hex_chars():
    d = _short_digest(b"hello")
    assert isinstance(d, str)
    assert len(d) == 16
    assert all(c in "0123456789abcdef" for c in d)


def test_short_digest_is_deterministic():
    assert _short_digest(b"hello") == _short_digest(b"hello")
    assert _short_digest(b"hello") != _short_digest(b"world")


def test_canonical_json_bytes_sorts_keys():
    a = _canonical_json_bytes({"b": 2, "a": 1})
    b = _canonical_json_bytes({"a": 1, "b": 2})
    assert a == b
    assert a == b'{"a": 1, "b": 2}'


def test_canonical_json_bytes_is_utf8_encoded():
    assert isinstance(_canonical_json_bytes({"x": 1}), bytes)
    assert _canonical_json_bytes({"name": "ümlaut"}).decode("utf-8") == '{"name": "ümlaut"}'


def test_assert_refusal_sentence_equal_passes():
    result = assert_refusal_sentence_equal()
    assert isinstance(result, InvariantResult)
    assert result.name == "refusal_sentence_byte_equal"
    assert "71" in result.detail  # the canonical sentence is 71 chars


def test_assert_refusal_sentence_equal_raises_on_drift(monkeypatch):
    """Mutate the imported tool_use_agent.verify.REFUSAL_SENTENCE so the
    cross-build comparison fails. Must raise InvariantError naming both."""
    import tool_use_agent.verify as tua_verify

    monkeypatch.setattr(tua_verify, "REFUSAL_SENTENCE", "drifted text")
    with pytest.raises(InvariantError, match="REFUSAL_SENTENCE drift"):
        assert_refusal_sentence_equal()


def test_assert_trace_helpers_behavior_passes():
    result = assert_trace_helpers_behavior()
    assert isinstance(result, InvariantResult)
    assert result.name == "trace_helpers_behavior_equivalent"
    # Detail names both builds and includes the digest values.
    assert "rag fp=" in result.detail
    assert "tua fp=" in result.detail


def test_assert_trace_helpers_behavior_detects_rag_fingerprint_drift(monkeypatch):
    """Patch rag_app.trace.compute_corpus_fingerprint to return a bogus
    digest and confirm InvariantError fires."""
    import rag_app.trace as rag_trace

    monkeypatch.setattr(rag_trace, "compute_corpus_fingerprint", lambda _: "0" * 16)
    with pytest.raises(InvariantError, match="rag-app compute_corpus_fingerprint drift"):
        assert_trace_helpers_behavior()


def test_assert_trace_helpers_behavior_detects_tua_fingerprint_drift(monkeypatch):
    import tool_use_agent.trace as tua_trace

    monkeypatch.setattr(tua_trace, "compute_corpus_fingerprint", lambda _: "f" * 16)
    with pytest.raises(InvariantError, match="tool-use-agent compute_corpus_fingerprint drift"):
        assert_trace_helpers_behavior()


def test_assert_trace_helpers_behavior_detects_rag_record_id_drift(monkeypatch):
    import rag_app.trace as rag_trace

    monkeypatch.setattr(rag_trace, "compute_record_id", lambda **_: "0" * 16)
    with pytest.raises(InvariantError, match="rag-app compute_record_id drift"):
        assert_trace_helpers_behavior()


def test_assert_trace_helpers_behavior_detects_tua_record_id_drift(monkeypatch):
    import tool_use_agent.trace as tua_trace

    monkeypatch.setattr(tua_trace, "compute_record_id", lambda **_: "0" * 16)
    with pytest.raises(InvariantError, match="tool-use-agent compute_record_id drift"):
        assert_trace_helpers_behavior()


def test_run_startup_invariants_returns_both_in_order():
    results = run_startup_invariants()
    assert len(results) == 2
    assert results[0].name == "refusal_sentence_byte_equal"
    assert results[1].name == "trace_helpers_behavior_equivalent"


def test_run_startup_invariants_propagates_first_failure(monkeypatch):
    """If invariant 1 fails, invariant 2 should not even run."""
    import tool_use_agent.verify as tua_verify

    monkeypatch.setattr(tua_verify, "REFUSAL_SENTENCE", "drifted")
    with pytest.raises(InvariantError, match="REFUSAL_SENTENCE drift"):
        run_startup_invariants()
