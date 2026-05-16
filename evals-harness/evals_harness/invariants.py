"""Startup invariants the harness asserts before any scoring.

Two cheap checks that prevent silent cross-build drift from producing a
plausible-but-wrong report:

1. ``REFUSAL_SENTENCE`` byte-equality. The rag-app build owns
   ``REFUSAL_SENTENCE`` in ``rag-app/rag_app/verify.py``; the
   tool-use-agent owns the same string in
   ``tool-use-agent/tool_use_agent/verify.py``. Per the
   iteration-11/14 lock, each build defines it independently and the
   harness asserts byte-equality at startup. A drift in either build
   would silently split one refusal bucket into two and skew the
   refusal-rate metric.

2. Trace-helper algorithm equivalence. The two builds independently
   implement ``compute_corpus_fingerprint`` and ``compute_record_id``
   (the signatures differ — rag-app hashes ``chunks.jsonl`` bytes,
   tool-use hashes canonical-JSON of the catalog list — but the
   underlying algorithm is the same: canonical-JSON / raw bytes →
   SHA-256 → 16-hex-char truncation). The harness asserts each build's
   helpers reproduce a digest computed independently in this module
   over a known fixture. A drift in either build (different hash,
   different truncation length, different canonicalization) is caught
   here rather than as a confused report.

Both invariants are deterministic and run in milliseconds. They never
hit the network or load corpus data.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _repo

_HEX_LEN = 16


class InvariantError(RuntimeError):
    """Named error a failed startup invariant raises so the CLI can
    fail-fast with a clear, attributable message."""


@dataclass(frozen=True)
class InvariantResult:
    name: str
    detail: str


def _short_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:_HEX_LEN]


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def assert_refusal_sentence_equal() -> InvariantResult:
    """Cross-build byte-equality on ``REFUSAL_SENTENCE``."""
    _repo.ensure_build_imports_on_path()

    from rag_app.verify import REFUSAL_SENTENCE as RAG_REFUSAL
    from tool_use_agent.verify import REFUSAL_SENTENCE as TUA_REFUSAL

    if RAG_REFUSAL != TUA_REFUSAL:
        raise InvariantError(
            "REFUSAL_SENTENCE drift between builds: "
            f"rag-app={RAG_REFUSAL!r} tool-use-agent={TUA_REFUSAL!r}"
        )
    return InvariantResult(
        name="refusal_sentence_byte_equal",
        detail=f"{len(RAG_REFUSAL)} chars, both builds",
    )


def assert_trace_helpers_behavior() -> InvariantResult:
    """Algorithm equivalence on ``compute_corpus_fingerprint`` and
    ``compute_record_id`` across the two builds.

    Signatures differ (rag-app: path on disk; tool-use: in-memory
    catalog), so we verify *algorithm* equivalence by computing the
    expected digest independently in this module for a fixture, then
    asserting each build's helper reproduces it.
    """
    _repo.ensure_build_imports_on_path()

    import rag_app.trace as rag_trace
    import tool_use_agent.trace as tua_trace

    # --- corpus_fingerprint (rag-app: bytes-on-disk) ---
    rag_blob = b'{"hello":"world"}\n'
    expected_rag_fp = _short_digest(rag_blob)
    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".jsonl", delete=False
    ) as fp:
        fp.write(rag_blob)
        tmp_path = Path(fp.name)
    try:
        got_rag_fp = rag_trace.compute_corpus_fingerprint(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    if got_rag_fp != expected_rag_fp:
        raise InvariantError(
            "rag-app compute_corpus_fingerprint drift: "
            f"expected {expected_rag_fp}, got {got_rag_fp}"
        )

    # --- corpus_fingerprint (tool-use: canonical-JSON of catalog) ---
    tua_catalog = [
        {
            "name": "fixture_tool",
            "description": "test tool for the invariant fixture",
            "input_schema": {"type": "object", "properties": {}},
        }
    ]
    expected_tua_fp = _short_digest(_canonical_json_bytes(tua_catalog))
    got_tua_fp = tua_trace.compute_corpus_fingerprint(tua_catalog)
    if got_tua_fp != expected_tua_fp:
        raise InvariantError(
            "tool-use-agent compute_corpus_fingerprint drift: "
            f"expected {expected_tua_fp}, got {got_tua_fp}"
        )

    # --- record_id (rag-app) ---
    rag_kwargs = {
        "question": "fixture question",
        "top_k": 5,
        "model": "fixture-model",
        "min_score": 1.5,
        "corpus_fingerprint": "deadbeefcafebabe",
        "mode": "dry-run",
    }
    rag_payload = {"schema": rag_trace.SCHEMA_VERSION, **rag_kwargs}
    expected_rag_rid = _short_digest(_canonical_json_bytes(rag_payload))
    got_rag_rid = rag_trace.compute_record_id(**rag_kwargs)
    if got_rag_rid != expected_rag_rid:
        raise InvariantError(
            "rag-app compute_record_id drift: "
            f"expected {expected_rag_rid}, got {got_rag_rid}"
        )

    # --- record_id (tool-use) ---
    tua_kwargs = {
        "question": "fixture question",
        "model": "fixture-model",
        "max_steps": 6,
        "mode": "dry-run",
        "corpus_fingerprint": "deadbeefcafebabe",
    }
    tua_payload = {"schema": tua_trace.SCHEMA_VERSION, **tua_kwargs}
    expected_tua_rid = _short_digest(_canonical_json_bytes(tua_payload))
    got_tua_rid = tua_trace.compute_record_id(**tua_kwargs)
    if got_tua_rid != expected_tua_rid:
        raise InvariantError(
            "tool-use-agent compute_record_id drift: "
            f"expected {expected_tua_rid}, got {got_tua_rid}"
        )

    return InvariantResult(
        name="trace_helpers_behavior_equivalent",
        detail=(
            f"rag fp={got_rag_fp} rid={got_rag_rid}; "
            f"tua fp={got_tua_fp} rid={got_tua_rid}"
        ),
    )


def run_startup_invariants() -> list[InvariantResult]:
    """Run all startup invariants in order. Raises on first failure."""
    return [
        assert_refusal_sentence_equal(),
        assert_trace_helpers_behavior(),
    ]
