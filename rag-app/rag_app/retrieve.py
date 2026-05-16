"""BM25 retrieval over the chunks.jsonl produced by `rag_app load`.

BM25 (Okapi BM25, Robertson/Sparck Jones formulation) is the long-running
baseline for sparse lexical retrieval. For a few-hundred-chunk markdown
corpus it is competitive with dense embeddings while needing zero external
dependencies — no tokenizer, no model download, no GPU. A future iteration
can add a dense reranker on top without changing this module's contract.

The module is a single in-memory index built fresh from chunks.jsonl on
each invocation; persistence would only matter at a corpus size where the
load itself is no longer cheap, and we are well below that.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# Standard BM25 hyperparameters. k1 controls term-frequency saturation,
# b controls length normalization. The Manning/Robertson defaults.
BM25_K1 = 1.5
BM25_B = 0.75

DEFAULT_TOP_K = 5

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercase + \\w+ tokenization. No stopword list — IDF handles it."""
    return _TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class IndexedChunk:
    id: str
    source: str
    span: tuple[int, int]
    text: str
    tokens: tuple[str, ...]
    term_freqs: dict[str, int]
    length: int


@dataclass(frozen=True)
class RetrievedChunk:
    rank: int
    score: float
    id: str
    source: str
    span: tuple[int, int]
    text: str


class BM25Index:
    """In-memory BM25 over a list of chunks loaded from chunks.jsonl.

    Build cost is O(total_tokens); query cost is O(|query| * |docs_with_term|).
    Both are negligible at our corpus size.
    """

    def __init__(self, chunks: Iterable[IndexedChunk], k1: float = BM25_K1, b: float = BM25_B):
        self.chunks: list[IndexedChunk] = list(chunks)
        if not self.chunks:
            raise ValueError("BM25Index requires at least one chunk")
        self.k1 = k1
        self.b = b
        self.n_docs = len(self.chunks)
        total_length = sum(c.length for c in self.chunks)
        self.avgdl = total_length / self.n_docs

        doc_freq: dict[str, int] = {}
        for chunk in self.chunks:
            for term in chunk.term_freqs:
                doc_freq[term] = doc_freq.get(term, 0) + 1
        # Robertson IDF with the +1 inside log so values stay non-negative
        # even for terms that appear in more than half the corpus.
        self.idf: dict[str, float] = {
            term: math.log(((self.n_docs - df + 0.5) / (df + 0.5)) + 1.0)
            for term, df in doc_freq.items()
        }

    def score(self, query_terms: list[str], chunk: IndexedChunk) -> float:
        total = 0.0
        length_norm = 1 - self.b + self.b * (chunk.length / self.avgdl)
        for term in query_terms:
            idf = self.idf.get(term)
            if idf is None:
                continue
            tf = chunk.term_freqs.get(term, 0)
            if tf == 0:
                continue
            total += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * length_norm)
        return total

    def query(self, question: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
        query_terms = tokenize(question)
        if not query_terms:
            return []
        scored: list[tuple[float, IndexedChunk]] = []
        for chunk in self.chunks:
            s = self.score(query_terms, chunk)
            if s > 0:
                scored.append((s, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:top_k]
        return [
            RetrievedChunk(
                rank=i + 1,
                score=s,
                id=c.id,
                source=c.source,
                span=c.span,
                text=c.text,
            )
            for i, (s, c) in enumerate(top)
        ]


def load_chunks(chunks_path: Path) -> list[IndexedChunk]:
    """Read a chunks.jsonl produced by `python -m rag_app load`."""
    if not chunks_path.is_file():
        raise FileNotFoundError(
            f"No chunks file at {chunks_path}. Run `python -m rag_app load` first."
        )
    indexed: list[IndexedChunk] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{chunks_path}:{line_no}: invalid JSON: {exc}")
            tokens = tokenize(rec["text"])
            tf: dict[str, int] = {}
            for tok in tokens:
                tf[tok] = tf.get(tok, 0) + 1
            indexed.append(
                IndexedChunk(
                    id=rec["id"],
                    source=rec["source"],
                    span=tuple(rec["span"]),
                    text=rec["text"],
                    tokens=tuple(tokens),
                    term_freqs=tf,
                    length=len(tokens),
                )
            )
    return indexed
