"""Tests for rag_app.generate: prompt construction + dry-run JSON contract.

No live calls. The Anthropic SDK is only imported inside call_claude, so the
build_prompt/format_chunk paths are key-free by construction. The JSON
contract test calls cmd_ask directly with an argparse Namespace and captures
stdout, exercising the same code path the CLI hits without subprocess
overhead or DEFAULT_CORPUS_FILES coupling.
"""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from rag_app.__main__ import DEFAULT_CHUNKS_PATH, cmd_ask
from rag_app.corpus import load_and_chunk, write_chunks
from rag_app.generate import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    SYSTEM_PROMPT,
    Prompt,
    build_prompt,
    format_chunk,
)
from rag_app.retrieve import DEFAULT_TOP_K, RetrievedChunk
from rag_app.verify import MIN_RETRIEVAL_SCORE, REFUSAL_SENTENCE

TINY_CORPUS_FILES: tuple[str, ...] = ("animals.md", "sub/cities.md")


def make_retrieved(rank: int, source: str, span: tuple[int, int], text: str) -> RetrievedChunk:
    return RetrievedChunk(
        rank=rank, score=4.2, id=f"{source}::{rank - 1}", source=source, span=span, text=text
    )


def _materialize_tiny_chunks(tiny_corpus_root: Path, tmp_path: Path) -> Path:
    chunks_path = tmp_path / "chunks.jsonl"
    chunks = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    write_chunks(chunks, chunks_path)
    return chunks_path


def _ask_namespace(**overrides) -> argparse.Namespace:
    """Build an argparse.Namespace matching the `ask` subparser's defaults."""
    defaults = dict(
        command="ask",
        question="placeholder",
        top_k=DEFAULT_TOP_K,
        chunks=DEFAULT_CHUNKS_PATH,
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        min_score=MIN_RETRIEVAL_SCORE,
        dry_run=False,
        json=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _capture_cmd_ask(args: argparse.Namespace, monkeypatch) -> str:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_ask(args)
    assert rc == 0
    return buf.getvalue()


def test_default_model_is_haiku_4_5():
    # Locked in DECISIONS.md; bumping the default is a deliberate decision.
    assert DEFAULT_MODEL == "claude-haiku-4-5-20251001"


def test_default_max_tokens():
    assert DEFAULT_MAX_TOKENS == 1024


def test_system_prompt_embeds_refusal_sentence():
    # The system prompt instructs the model to use the same refusal bytes
    # the verify module emits when the BM25 top score is below threshold.
    assert REFUSAL_SENTENCE in SYSTEM_PROMPT


def test_system_prompt_documents_citation_format():
    assert "[<source>#<start>-<end>]" in SYSTEM_PROMPT


def test_format_chunk_shape():
    c = make_retrieved(1, "animals.md", (0, 120), "Pangolins are mammals.")
    formatted = format_chunk(c)
    assert formatted.startswith('<chunk source="animals.md" span="0-120">')
    assert formatted.endswith("</chunk>")
    assert "Pangolins are mammals." in formatted


def test_build_prompt_with_chunks_is_pure():
    chunks = [
        make_retrieved(1, "animals.md", (0, 50), "Pangolins eat ants."),
        make_retrieved(2, "sub/cities.md", (0, 80), "Reykjavik is Iceland's capital."),
    ]
    prompt = build_prompt("What do pangolins eat?", chunks)
    assert isinstance(prompt, Prompt)
    assert prompt.system == SYSTEM_PROMPT
    assert "What do pangolins eat?" in prompt.user
    assert "Pangolins eat ants." in prompt.user
    assert "Reykjavik" in prompt.user
    assert '<chunk source="animals.md"' in prompt.user
    # And it's deterministic on the same inputs.
    assert build_prompt("What do pangolins eat?", chunks) == prompt


def test_build_prompt_with_no_chunks_signals_empty_context():
    prompt = build_prompt("Anything?", [])
    assert "(no chunks were retrieved)" in prompt.user
    # No chunk tags must appear when retrieval was empty.
    assert "<chunk" not in prompt.user


def test_ask_dry_run_json_contract(tiny_corpus_root: Path, tmp_path: Path, monkeypatch):
    """Dry-run JSON contract: schema/field types only, no model call."""
    chunks_path = _materialize_tiny_chunks(tiny_corpus_root, tmp_path)
    args = _ask_namespace(
        question="What do pangolins eat?",
        chunks=str(chunks_path),
        min_score=0.0,
        dry_run=True,
        json=True,
    )
    stdout = _capture_cmd_ask(args, monkeypatch)
    payload = json.loads(stdout)

    # Schema + identity fields
    assert payload["schema_version"] == "rag-app.ask.v1"
    assert isinstance(payload["record_id"], str) and len(payload["record_id"]) == 16
    assert isinstance(payload["generated_at"], str)
    assert payload["generated_at"].endswith("Z")
    assert isinstance(payload["corpus_fingerprint"], str)
    assert len(payload["corpus_fingerprint"]) == 16

    # Query echo
    assert payload["question"] == "What do pangolins eat?"
    assert payload["top_k"] == DEFAULT_TOP_K
    assert payload["model"] == DEFAULT_MODEL
    assert payload["min_score"] == 0.0
    assert isinstance(payload["top_score"], (int, float))

    # No API key + --dry-run together → mode=dry-run
    assert payload["mode"] == "dry-run"

    # Retrieved list shape
    assert isinstance(payload["retrieved"], list)
    assert len(payload["retrieved"]) >= 1
    r0 = payload["retrieved"][0]
    for key in ("rank", "score", "id", "source", "span", "text"):
        assert key in r0
    assert isinstance(r0["span"], list) and len(r0["span"]) == 2
    assert isinstance(r0["rank"], int)
    assert isinstance(r0["score"], (int, float))

    # Prompt block
    assert payload["prompt"]["system"] == SYSTEM_PROMPT
    assert "Context chunks" in payload["prompt"]["user"]

    # Dry-run does not produce an answer or verification block
    assert payload["answer"] is None
    assert payload["verification"] is None


def test_ask_refusal_path_emits_refusal_sentence(tiny_corpus_root: Path, tmp_path: Path, monkeypatch):
    """Setting min_score above the top BM25 score must short-circuit to
    the canonical refusal sentence with no model call."""
    chunks_path = _materialize_tiny_chunks(tiny_corpus_root, tmp_path)
    args = _ask_namespace(
        question="totally irrelevant query about quasars",
        chunks=str(chunks_path),
        min_score=99.0,
        json=True,
    )
    stdout = _capture_cmd_ask(args, monkeypatch)
    payload = json.loads(stdout)
    assert payload["mode"] == "refused-low-score"
    assert payload["answer"]["text"] == REFUSAL_SENTENCE
    assert payload["answer"]["reason"] == "low_retrieval_score"
    assert payload["verification"] is None


def test_ask_dry_run_text_output(tiny_corpus_root: Path, tmp_path: Path, monkeypatch):
    """The non-JSON dry-run path prints the prompt and a dry-run marker."""
    chunks_path = _materialize_tiny_chunks(tiny_corpus_root, tmp_path)
    args = _ask_namespace(
        question="What do pangolins eat?",
        chunks=str(chunks_path),
        min_score=0.0,
        dry_run=True,
    )
    stdout = _capture_cmd_ask(args, monkeypatch)
    assert "Mode: dry-run" in stdout
    assert "(dry-run: no model call made)" in stdout
    assert "--- prompt.system ---" in stdout
    assert "--- prompt.user ---" in stdout


def test_ask_refusal_text_output(tiny_corpus_root: Path, tmp_path: Path, monkeypatch):
    chunks_path = _materialize_tiny_chunks(tiny_corpus_root, tmp_path)
    args = _ask_namespace(
        question="totally irrelevant query about quasars",
        chunks=str(chunks_path),
        min_score=99.0,
    )
    stdout = _capture_cmd_ask(args, monkeypatch)
    assert "Mode: refused-low-score" in stdout
    assert REFUSAL_SENTENCE in stdout


def test_call_claude_lazy_import_does_not_run_at_module_load():
    """Importing rag_app.generate must not import anthropic — the SDK
    import lives inside call_claude so dry-run paths work key-free."""
    import importlib

    mod = importlib.import_module("rag_app.generate")
    # No Anthropic client class bound at module level.
    assert not hasattr(mod, "Anthropic")
