"""Tests for rag_app.retrieve: BM25 ranking on a fixture corpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_app.corpus import load_and_chunk, write_chunks
from rag_app.retrieve import (
    BM25_B,
    BM25_K1,
    BM25Index,
    IndexedChunk,
    load_chunks,
    tokenize,
)

TINY_CORPUS_FILES: tuple[str, ...] = ("animals.md", "sub/cities.md")


@pytest.fixture(scope="session")
def fixture_chunks_path(tiny_corpus_root: Path, tmp_path_factory) -> Path:
    """Materialize the tiny-corpus chunks.jsonl once per session."""
    out_dir = tmp_path_factory.mktemp("tiny_chunks")
    chunks = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    out = out_dir / "chunks.jsonl"
    write_chunks(chunks, out)
    return out


@pytest.fixture
def index(fixture_chunks_path: Path) -> BM25Index:
    return BM25Index(load_chunks(fixture_chunks_path))


def test_tokenize_lowercases_and_splits_word_chars():
    assert tokenize("Hello, World!") == ["hello", "world"]
    assert tokenize("BM25 ranks docs.") == ["bm25", "ranks", "docs"]
    assert tokenize("") == []


def test_tokenize_unicode_word_chars():
    # \w is Unicode-aware by default
    assert tokenize("Köln Sao_Paulo") == ["köln", "sao_paulo"]


def test_load_chunks_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_chunks(tmp_path / "nope.jsonl")


def test_load_chunks_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "chunks.jsonl"
    rec = {"id": "a::0", "source": "a", "span": [0, 5], "text": "hello world"}
    p.write_text(json.dumps(rec) + "\n\n" + json.dumps(rec) + "\n", encoding="utf-8")
    indexed = load_chunks(p)
    assert len(indexed) == 2
    assert all(isinstance(c, IndexedChunk) for c in indexed)


def test_load_chunks_invalid_json_raises(tmp_path: Path):
    p = tmp_path / "bad.jsonl"
    p.write_text("{not valid json\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_chunks(p)


def test_indexed_chunk_term_freqs_match_tokens(fixture_chunks_path: Path):
    indexed = load_chunks(fixture_chunks_path)
    for chunk in indexed:
        # tf totals must equal token length
        assert sum(chunk.term_freqs.values()) == chunk.length
        # every token present in tf
        for tok in chunk.tokens:
            assert tok in chunk.term_freqs


def test_bm25_empty_corpus_raises():
    with pytest.raises(ValueError):
        BM25Index([])


def test_bm25_defaults_are_locked():
    # k1 and b are documented contract; any change is a deliberate retune.
    assert BM25_K1 == 1.5
    assert BM25_B == 0.75


def test_bm25_top_result_matches_animals_query(index: BM25Index):
    results = index.query("Which animals regenerate limbs?", top_k=3)
    assert results, "BM25 must return at least one match for a known query"
    assert results[0].source == "animals.md"
    # axolotl chunk contains "regenerate limbs" — it must be #1
    assert "axolotl" in results[0].text.lower()


def test_bm25_top_result_matches_cities_query(index: BM25Index):
    results = index.query("What is the capital of Iceland?", top_k=3)
    assert results
    assert results[0].source == "sub/cities.md"
    assert "reykjavik" in results[0].text.lower()


def test_bm25_results_have_monotone_descending_scores(index: BM25Index):
    # Query terms from both fixture files so multiple chunks score >0.
    results = index.query("pangolins Reykjavik", top_k=5)
    assert len(results) >= 2
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert all(s > 0 for s in scores)


def test_bm25_results_have_sequential_ranks_starting_at_1(index: BM25Index):
    results = index.query("pangolins Reykjavik", top_k=5)
    assert results
    for i, r in enumerate(results, start=1):
        assert r.rank == i


def test_bm25_empty_question_returns_empty(index: BM25Index):
    assert index.query("", top_k=5) == []
    assert index.query("!!! @@@ ###", top_k=5) == []


def test_bm25_oov_query_returns_empty(index: BM25Index):
    # No fixture text talks about quasars or stellar nucleosynthesis.
    results = index.query("quasar nucleosynthesis", top_k=5)
    assert results == []


def test_bm25_respects_top_k(index: BM25Index):
    results = index.query("the", top_k=1)
    assert len(results) <= 1


def test_bm25_score_is_deterministic(index: BM25Index):
    a = index.query("Reykjavik Iceland", top_k=3)
    b = index.query("Reykjavik Iceland", top_k=3)
    assert [(r.rank, r.id, r.score) for r in a] == [
        (r.rank, r.id, r.score) for r in b
    ]
