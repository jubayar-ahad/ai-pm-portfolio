"""Tests for rag_app.corpus: chunking shape + determinism + helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_app.corpus import (
    DEFAULT_CHUNK_WORDS,
    DEFAULT_OVERLAP_WORDS,
    Chunk,
    Paragraph,
    chunk_paragraphs,
    find_repo_root,
    load_and_chunk,
    split_paragraphs,
    write_chunks,
)

TINY_CORPUS_FILES: tuple[str, ...] = ("animals.md", "sub/cities.md")


def test_split_paragraphs_preserves_offsets():
    text = "First paragraph.\n\nSecond paragraph here.\n\nThird."
    paras = split_paragraphs(text)
    assert [p.text for p in paras] == [
        "First paragraph.",
        "Second paragraph here.",
        "Third.",
    ]
    # Offsets must index into the original text and reproduce the paragraph
    # text exactly.
    for p in paras:
        assert text[p.start : p.end].strip() == p.text


def test_split_paragraphs_skips_blank_blocks():
    text = "\n\n\nReal paragraph.\n\n\n\nAnother one.\n\n\n"
    paras = split_paragraphs(text)
    assert len(paras) == 2
    assert paras[0].text.strip() == "Real paragraph."
    assert paras[1].text.strip() == "Another one."


def test_paragraph_word_count():
    p = Paragraph("one two three four five", 0, 22)
    assert p.word_count == 5


def test_chunk_paragraphs_emits_at_least_one_chunk():
    paras = [
        Paragraph("alpha beta gamma", 0, 17),
        Paragraph("delta epsilon", 19, 32),
    ]
    chunks = list(chunk_paragraphs(paras, source="src.md", chunk_words=10, overlap_words=2))
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].id == "src.md::0"
    assert chunks[0].source == "src.md"


def test_chunk_paragraphs_oversized_paragraph_still_emitted():
    big = " ".join(["word"] * 50)
    paras = [Paragraph(big, 0, len(big))]
    chunks = list(chunk_paragraphs(paras, source="big.md", chunk_words=10, overlap_words=2))
    assert len(chunks) == 1
    assert chunks[0].word_count == 50


def test_chunk_paragraphs_overlap_carries_paragraphs():
    paras = [
        Paragraph("a a a a", 0, 7),
        Paragraph("b b b b", 9, 16),
        Paragraph("c c c c", 18, 25),
        Paragraph("d d d d", 27, 34),
    ]
    chunks = list(chunk_paragraphs(paras, source="x.md", chunk_words=8, overlap_words=4))
    # First chunk takes paras 0,1 (8 words). Then overlap=4 carries para 1
    # (4 words) into the next chunk, which then takes para 2.
    assert len(chunks) >= 2
    assert chunks[0].id == "x.md::0"
    assert chunks[1].id == "x.md::1"
    # Overlap means the boundary paragraph appears in both chunks.
    assert "b b b b" in chunks[0].text
    assert "b b b b" in chunks[1].text


def test_chunk_paragraphs_rejects_bad_args():
    paras = [Paragraph("x", 0, 1)]
    with pytest.raises(ValueError):
        list(chunk_paragraphs(paras, source="s.md", chunk_words=0, overlap_words=0))
    with pytest.raises(ValueError):
        list(chunk_paragraphs(paras, source="s.md", chunk_words=10, overlap_words=10))
    with pytest.raises(ValueError):
        list(chunk_paragraphs(paras, source="s.md", chunk_words=10, overlap_words=-1))


def test_load_and_chunk_runs_on_tiny_corpus(tiny_corpus_root: Path):
    chunks = load_and_chunk(
        corpus_root=tiny_corpus_root,
        files=TINY_CORPUS_FILES,
        chunk_words=DEFAULT_CHUNK_WORDS,
        overlap_words=DEFAULT_OVERLAP_WORDS,
    )
    assert len(chunks) >= 2
    sources = {c.source for c in chunks}
    assert sources == set(TINY_CORPUS_FILES)
    for c in chunks:
        assert c.id.startswith(c.source + "::")
        assert c.word_count > 0
        assert c.span[0] < c.span[1]
        assert c.text.strip() != ""


def test_load_and_chunk_is_deterministic(tiny_corpus_root: Path):
    first = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    second = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    assert first == second


def test_load_and_chunk_missing_file_raises(tiny_corpus_root: Path):
    with pytest.raises(FileNotFoundError):
        load_and_chunk(corpus_root=tiny_corpus_root, files=("does_not_exist.md",))


def test_write_chunks_roundtrips_jsonl(tiny_corpus_root: Path, tmp_path: Path):
    chunks = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    out = tmp_path / "chunks.jsonl"
    write_chunks(chunks, out)
    assert out.is_file()
    with out.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    assert len(records) == len(chunks)
    for rec, chunk in zip(records, chunks):
        assert rec["id"] == chunk.id
        assert rec["source"] == chunk.source
        assert rec["text"] == chunk.text
        assert tuple(rec["span"]) == chunk.span


def test_write_chunks_creates_parent_dirs(tiny_corpus_root: Path, tmp_path: Path):
    chunks = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    out = tmp_path / "nested" / "deeper" / "chunks.jsonl"
    write_chunks(chunks, out)
    assert out.is_file()


def test_find_repo_root_locates_anchor(tiny_corpus_root: Path):
    nested = tiny_corpus_root / "sub"
    assert find_repo_root(nested) == tiny_corpus_root
    assert find_repo_root(tiny_corpus_root) == tiny_corpus_root


def test_find_repo_root_raises_when_anchor_missing(tmp_path: Path):
    # tmp_path has no OBJECTIVE.md above it (pytest tmp dirs live under /tmp
    # or /private/tmp, neither of which contains an OBJECTIVE.md anchor).
    with pytest.raises(FileNotFoundError):
        find_repo_root(tmp_path)
