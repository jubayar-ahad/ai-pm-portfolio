"""Corpus loader and paragraph-aware chunker for the rag-app demo.

Reads the v1 corpus (a fixed list of repo markdown files), splits each file
into paragraph-aware chunks of bounded word count with paragraph-level
overlap, and writes a JSONL file the embedding-index iteration will consume.

Word counts are used as a stdlib-only stand-in for token counts so the loader
runs without a tokenizer dependency. For English markdown this is close
enough; the embedding step can re-measure if it cares.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_CORPUS_FILES: tuple[str, ...] = (
    "OBJECTIVE.md",
    "DECISIONS.md",
    "templates/INTERVIEW_TRACKER.md",
    "rag-app/README.md",
)

DEFAULT_CHUNK_WORDS = 400
DEFAULT_OVERLAP_WORDS = 80

_PARAGRAPH_SPLIT = re.compile(r"\n{2,}")


@dataclass(frozen=True)
class Paragraph:
    text: str
    start: int  # inclusive char offset in source file
    end: int    # exclusive char offset in source file

    @property
    def word_count(self) -> int:
        return len(self.text.split())


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    span: tuple[int, int]
    word_count: int
    text: str


def split_paragraphs(text: str) -> list[Paragraph]:
    """Split on one-or-more blank lines, preserving original char offsets."""
    paras: list[Paragraph] = []
    cursor = 0
    for match in _PARAGRAPH_SPLIT.finditer(text):
        block = text[cursor:match.start()]
        if block.strip():
            paras.append(Paragraph(block, cursor, match.start()))
        cursor = match.end()
    tail = text[cursor:]
    if tail.strip():
        paras.append(Paragraph(tail, cursor, len(text)))
    return paras


def chunk_paragraphs(
    paragraphs: list[Paragraph],
    source: str,
    chunk_words: int,
    overlap_words: int,
) -> Iterator[Chunk]:
    """Greedy-pack paragraphs into chunks; carry overlap at paragraph boundary.

    A paragraph larger than chunk_words is emitted as its own oversized chunk
    rather than mid-split, on the theory that mid-paragraph splits hurt
    retrieval more than an occasional fat chunk in this corpus.
    """
    if chunk_words <= 0:
        raise ValueError("chunk_words must be positive")
    if not 0 <= overlap_words < chunk_words:
        raise ValueError("overlap_words must be in [0, chunk_words)")

    buffer: list[Paragraph] = []
    buffer_words = 0
    chunk_idx = 0

    def emit() -> Chunk:
        nonlocal chunk_idx
        chunk = Chunk(
            id=f"{source}::{chunk_idx}",
            source=source,
            span=(buffer[0].start, buffer[-1].end),
            word_count=sum(p.word_count for p in buffer),
            text="\n\n".join(p.text for p in buffer),
        )
        chunk_idx += 1
        return chunk

    for para in paragraphs:
        if buffer and buffer_words + para.word_count > chunk_words:
            yield emit()
            carry: list[Paragraph] = []
            carry_words = 0
            for p in reversed(buffer):
                if carry_words + p.word_count > overlap_words:
                    break
                carry.insert(0, p)
                carry_words += p.word_count
            buffer = carry
            buffer_words = carry_words
        buffer.append(para)
        buffer_words += para.word_count

    if buffer:
        yield emit()


def find_repo_root(start: Path) -> Path:
    """Walk up from `start` looking for OBJECTIVE.md, the repo's anchor file."""
    for candidate in [start, *start.parents]:
        if (candidate / "OBJECTIVE.md").is_file():
            return candidate
    raise FileNotFoundError(
        f"Could not locate repo root above {start} (no OBJECTIVE.md found)"
    )


def load_and_chunk(
    corpus_root: Path,
    files: tuple[str, ...] = DEFAULT_CORPUS_FILES,
    chunk_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for relative in files:
        path = corpus_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Corpus file missing: {path}")
        text = path.read_text(encoding="utf-8")
        paragraphs = split_paragraphs(text)
        chunks.extend(
            chunk_paragraphs(paragraphs, relative, chunk_words, overlap_words)
        )
    return chunks


def write_chunks(chunks: list[Chunk], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False))
            f.write("\n")
