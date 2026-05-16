"""Refusal threshold and citation verification for the `ask` slice.

Two responsibilities, both mechanical enforcement of rules locked in
DECISIONS.md for the generation slice:

1. **Refusal threshold.** If the BM25 top score is below
   ``MIN_RETRIEVAL_SCORE`` (or no chunks were retrieved at all), the
   ``ask`` CLI short-circuits the model call and emits the canonical
   refusal sentence directly. The sentence is identical to the one the
   system prompt instructs the model to use on weak context, so the
   evals harness can treat both refusal paths as one bucket.

2. **Citation verification.** Parse every ``[<source>#<start>-<end>]``
   citation out of the model's answer and check that each one resolves
   to a chunk that was actually retrieved for this query. A citation is
   "verified" when (source, start, end) exactly matches the source/span
   of one of the retrieved chunks. Anything else (wrong source, span
   that doesn't match any retrieved chunk, malformed citation) is
   flagged. We deliberately verify against the *retrieved* chunks, not
   the full corpus, because the system prompt forbids citing context
   the model wasn't given.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from rag_app.retrieve import RetrievedChunk

REFUSAL_SENTENCE = (
    "I don't have enough information in the provided context to answer this."
)

# Threshold chosen against the iteration-5 validation runs: relevant
# in-corpus questions score >= ~3, while irrelevant queries
# ("capital of France") top out below 1.4. 1.5 leaves headroom on both
# sides; the evals harness can retune once it exists.
MIN_RETRIEVAL_SCORE = 1.5

# Citation grammar locked in DECISIONS.md: [<source>#<start>-<end>].
# `#` is the separator so the source field can contain `::` (used inside
# chunk ids) without ambiguity. Source may contain any character except
# `#` or `]`.
CITATION_RE = re.compile(r"\[([^#\]]+)#(\d+)-(\d+)\]")


@dataclass(frozen=True)
class Citation:
    source: str
    start: int
    end: int
    raw: str
    resolved: bool


@dataclass(frozen=True)
class VerificationReport:
    citations: tuple[Citation, ...]
    unresolved: tuple[Citation, ...]

    @property
    def total(self) -> int:
        return len(self.citations)

    @property
    def resolved_count(self) -> int:
        return sum(1 for c in self.citations if c.resolved)

    @property
    def all_resolved(self) -> bool:
        return self.total > 0 and not self.unresolved


def should_refuse(
    retrieved: list[RetrievedChunk],
    threshold: float = MIN_RETRIEVAL_SCORE,
) -> bool:
    """True iff retrieval is too weak to justify a model call."""
    if not retrieved:
        return True
    return retrieved[0].score < threshold


def parse_citations(answer: str) -> list[Citation]:
    """Extract every ``[<source>#<start>-<end>]`` citation from the answer.

    `resolved` is left False here; ``verify_citations`` fills it in once
    the retrieved chunks are known.
    """
    citations: list[Citation] = []
    for match in CITATION_RE.finditer(answer):
        source = match.group(1).strip()
        start = int(match.group(2))
        end = int(match.group(3))
        citations.append(
            Citation(
                source=source,
                start=start,
                end=end,
                raw=match.group(0),
                resolved=False,
            )
        )
    return citations


def verify_citations(
    answer: str,
    retrieved: Iterable[RetrievedChunk],
) -> VerificationReport:
    """Parse + check every citation in ``answer`` against the retrieved set.

    A citation resolves when its (source, start, end) tuple matches the
    source and span of a chunk that was retrieved for this query. Span
    equality (not containment) is required so the model cannot make up
    sub-spans the chunker did not emit.
    """
    retrieved_spans = {
        (chunk.source, chunk.span[0], chunk.span[1]) for chunk in retrieved
    }
    parsed = parse_citations(answer)
    citations = tuple(
        Citation(
            source=c.source,
            start=c.start,
            end=c.end,
            raw=c.raw,
            resolved=(c.source, c.start, c.end) in retrieved_spans,
        )
        for c in parsed
    )
    unresolved = tuple(c for c in citations if not c.resolved)
    return VerificationReport(citations=citations, unresolved=unresolved)
