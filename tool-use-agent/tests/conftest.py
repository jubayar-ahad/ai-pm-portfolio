"""Shared pytest fixtures for the tool-use-agent suite.

Tests run with `pytest` from the tool-use-agent/ directory and target the
installed `tool_use_agent` package (editable install assumed). No network
access, no API keys — every test uses fixture files under tests/fixtures/
or in-memory data structures. The Anthropic SDK is stubbed via
sys.modules monkeypatching where needed (test_agent.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def tiny_repo_root(fixtures_dir: Path) -> Path:
    """Self-contained fixture repo with a stub OBJECTIVE.md anchor."""
    return fixtures_dir / "tiny_repo"
