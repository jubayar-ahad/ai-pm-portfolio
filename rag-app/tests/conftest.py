"""Shared pytest fixtures for the rag-app suite.

Tests run with `pytest` from the rag-app/ directory and target the installed
`rag_app` package (editable install assumed). No network access, no API
keys — every test uses fixture files under tests/fixtures/ or in-memory
data structures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def tiny_corpus_root(fixtures_dir: Path) -> Path:
    """Self-contained fixture corpus with a stub OBJECTIVE.md anchor."""
    return fixtures_dir / "tiny_corpus"
