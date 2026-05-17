"""Shared pytest fixtures for the evals-harness suite.

Tests run with `pytest` from the evals-harness/ directory and target the
installed `evals_harness` package (editable install assumed). No network
access, no API keys — every test uses fixture files under tests/fixtures/
or in-memory data structures. The sibling builds (`rag_app`,
`tool_use_agent`) are added to sys.path by the harness's _repo module at
import time, so they are import-resolvable without an editable install
of those packages.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def queries_tiny_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "queries_tiny.jsonl"


@pytest.fixture(scope="session")
def traces_rag_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "traces_rag.jsonl"


@pytest.fixture(scope="session")
def traces_tua_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "traces_tua.jsonl"


@pytest.fixture
def minimal_label() -> dict:
    """A label record with the canonical 9-key shape.

    Each test mutates a copy if it needs to exercise a specific failure
    mode (extra key / missing key / bad enum / mismatched fingerprint
    keys). Default values satisfy every validation check.
    """
    return {
        "id": "q-test-001",
        "question": "What is the canonical refusal sentence?",
        "shape": "in_corpus",
        "expected_outcome": "answer",
        "applies_to": ["rag-app.ask.v1", "tool-use-agent.ask.v1"],
        "expected_citation_source": "DECISIONS.md",
        "expected_first_tool": None,
        "corpus_fingerprint_at_label": {
            "rag-app.ask.v1": "deadbeef00000001",
            "tool-use-agent.ask.v1": "deadbeef00000002",
        },
        "notes": "",
    }


@pytest.fixture
def minimal_rag_trace() -> dict:
    """A rag-app trace with the canonical schema_version + required fields."""
    return {
        "schema_version": "rag-app.ask.v1",
        "record_id": "rag-rec-001",
        "corpus_fingerprint": "deadbeef00000001",
        "question": "What is the canonical refusal sentence?",
        "mode": "live",
        "answer": {
            "text": "The canonical refusal sentence is locked in DECISIONS.md.",
            "input_tokens": 120,
            "output_tokens": 30,
        },
        "verification": {
            "total": 1,
            "resolved": 1,
            "all_resolved": True,
            "citations": [{"source": "DECISIONS.md", "resolved": True}],
        },
    }


@pytest.fixture
def minimal_tua_trace() -> dict:
    """A tool-use-agent trace with the canonical schema_version + required fields."""
    return {
        "schema_version": "tool-use-agent.ask.v1",
        "record_id": "tua-rec-001",
        "corpus_fingerprint": "deadbeef00000002",
        "question": "What is the canonical refusal sentence?",
        "mode": "live",
        "final_text": "The canonical refusal sentence lives in DECISIONS.md.",
        "refusal_reason": None,
        "stop_reason": "end_turn",
        "steps_taken": 2,
        "max_steps": 6,
        "input_tokens": 200,
        "output_tokens": 50,
        "tool_calls": [
            {"tool": "read_repo_file", "input": {"path": "DECISIONS.md"}, "latency_ms": 12},
            {"tool": "grep_repo", "input": {"pattern": "refusal"}, "latency_ms": 18},
        ],
    }
