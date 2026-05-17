"""Tests for rag_app.verify: refusal threshold + citation parser/verifier."""

from __future__ import annotations

import pytest

from rag_app.retrieve import RetrievedChunk
from rag_app.verify import (
    CITATION_RE,
    MIN_RETRIEVAL_SCORE,
    REFUSAL_SENTENCE,
    parse_citations,
    should_refuse,
    verify_citations,
)


def make_retrieved(rank: int, score: float, source: str, span: tuple[int, int]) -> RetrievedChunk:
    return RetrievedChunk(
        rank=rank,
        score=score,
        id=f"{source}::{rank - 1}",
        source=source,
        span=span,
        text="(text body irrelevant for verify tests)",
    )


def test_refusal_sentence_is_byte_identical():
    # The sentence is part of the cross-build contract (rag-app + tool-use-agent
    # both ship the same bytes). Any edit must be deliberate.
    assert REFUSAL_SENTENCE == (
        "I don't have enough information in the provided context to answer this."
    )
    assert len(REFUSAL_SENTENCE) == 71


def test_min_retrieval_score_default_locked():
    assert MIN_RETRIEVAL_SCORE == 1.5


def test_should_refuse_empty_retrieval():
    assert should_refuse([]) is True


def test_should_refuse_below_threshold():
    chunks = [make_retrieved(1, 0.9, "a.md", (0, 10))]
    assert should_refuse(chunks) is True


def test_should_not_refuse_at_or_above_threshold():
    chunks = [make_retrieved(1, MIN_RETRIEVAL_SCORE, "a.md", (0, 10))]
    assert should_refuse(chunks) is False
    chunks = [make_retrieved(1, 4.2, "a.md", (0, 10))]
    assert should_refuse(chunks) is False


def test_should_refuse_respects_custom_threshold():
    chunks = [make_retrieved(1, 2.0, "a.md", (0, 10))]
    assert should_refuse(chunks, threshold=3.0) is True
    assert should_refuse(chunks, threshold=1.0) is False


def test_parse_citations_happy_path():
    answer = (
        "Pangolins eat ants [animals.md#0-120]. Octopuses have three hearts "
        "[animals.md#125-260]."
    )
    citations = parse_citations(answer)
    assert len(citations) == 2
    assert citations[0].source == "animals.md"
    assert citations[0].start == 0
    assert citations[0].end == 120
    assert citations[0].raw == "[animals.md#0-120]"
    assert citations[0].resolved is False  # parse_citations does not resolve
    assert citations[1].source == "animals.md"
    assert citations[1].start == 125


def test_parse_citations_handles_nested_path_sources():
    answer = "Reykjavik is Iceland's capital [sub/cities.md#0-90]."
    [c] = parse_citations(answer)
    assert c.source == "sub/cities.md"
    assert c.start == 0
    assert c.end == 90


def test_parse_citations_no_citations_returns_empty():
    answer = "This answer cites nothing at all."
    assert parse_citations(answer) == []


def test_parse_citations_ignores_malformed_brackets():
    # Missing the `#`, missing end number, wrong separator
    answer = "[animals.md-0-120] [animals.md#0] [animals.md|0-120]"
    assert parse_citations(answer) == []


def test_citation_regex_groups_round_trip():
    m = CITATION_RE.search("text [src/a.md#12-34] more")
    assert m is not None
    assert m.group(1) == "src/a.md"
    assert m.group(2) == "12"
    assert m.group(3) == "34"


def test_verify_citations_marks_all_resolved_when_spans_match():
    retrieved = [
        make_retrieved(1, 4.0, "animals.md", (0, 120)),
        make_retrieved(2, 3.0, "animals.md", (125, 260)),
    ]
    answer = "Pangolins [animals.md#0-120]. Octopuses [animals.md#125-260]."
    report = verify_citations(answer, retrieved)
    assert report.total == 2
    assert report.resolved_count == 2
    assert report.all_resolved is True
    assert report.unresolved == ()


def test_verify_citations_flags_unresolved_spans():
    retrieved = [make_retrieved(1, 4.0, "animals.md", (0, 120))]
    # Span that doesn't match any retrieved chunk
    answer = "Made-up claim [animals.md#999-1000]."
    report = verify_citations(answer, retrieved)
    assert report.total == 1
    assert report.resolved_count == 0
    assert report.all_resolved is False
    assert len(report.unresolved) == 1
    assert report.unresolved[0].raw == "[animals.md#999-1000]"


def test_verify_citations_flags_wrong_source():
    retrieved = [make_retrieved(1, 4.0, "animals.md", (0, 120))]
    # Same span but wrong source
    answer = "Wrong source [cities.md#0-120]."
    report = verify_citations(answer, retrieved)
    assert report.all_resolved is False
    assert report.unresolved[0].source == "cities.md"


def test_verify_citations_requires_span_equality_not_containment():
    # Sub-span of a retrieved chunk must NOT resolve — the chunker did not
    # emit that span, so the model must not invent it.
    retrieved = [make_retrieved(1, 4.0, "animals.md", (0, 120))]
    answer = "Sub-span claim [animals.md#10-50]."
    report = verify_citations(answer, retrieved)
    assert report.all_resolved is False


def test_verify_citations_empty_answer():
    retrieved = [make_retrieved(1, 4.0, "animals.md", (0, 120))]
    report = verify_citations("", retrieved)
    assert report.total == 0
    assert report.resolved_count == 0
    assert report.unresolved == ()
    # all_resolved requires total>0 — defined False for the empty case
    assert report.all_resolved is False


def test_verify_citations_mixed_resolved_and_unresolved():
    retrieved = [
        make_retrieved(1, 4.0, "animals.md", (0, 120)),
        make_retrieved(2, 3.0, "sub/cities.md", (0, 90)),
    ]
    answer = (
        "Good cite [animals.md#0-120]. "
        "Hallucinated [animals.md#9999-10000]. "
        "Another good cite [sub/cities.md#0-90]."
    )
    report = verify_citations(answer, retrieved)
    assert report.total == 3
    assert report.resolved_count == 2
    assert report.all_resolved is False
    assert len(report.unresolved) == 1
