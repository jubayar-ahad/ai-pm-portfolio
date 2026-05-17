"""Tests for evals_harness._repo: repo-root walk + sys.path setup."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from evals_harness import _repo


def test_find_repo_root_locates_real_repo():
    """The harness's own _repo.py lives under <repo>/evals-harness/evals_harness/.
    Default-arg walk should resolve to the real repo root (the one with
    OBJECTIVE.md at top-level)."""
    root = _repo.find_repo_root()
    assert (root / "OBJECTIVE.md").is_file()
    assert (root / "evals-harness").is_dir()
    assert (root / "rag-app").is_dir()
    assert (root / "tool-use-agent").is_dir()


def test_find_repo_root_with_explicit_start(tmp_path: Path):
    """A custom start path with a stub OBJECTIVE.md should anchor there."""
    (tmp_path / "OBJECTIVE.md").write_text("# stub\n", encoding="utf-8")
    sub = tmp_path / "deep" / "nested"
    sub.mkdir(parents=True)
    got = _repo.find_repo_root(start=sub)
    assert got == tmp_path.resolve()


def test_find_repo_root_walks_up_until_objective(tmp_path: Path):
    (tmp_path / "OBJECTIVE.md").write_text("x\n", encoding="utf-8")
    leaf = tmp_path / "a" / "b" / "c" / "leaf.txt"
    leaf.parent.mkdir(parents=True)
    leaf.write_text("", encoding="utf-8")
    assert _repo.find_repo_root(start=leaf) == tmp_path.resolve()


def test_find_repo_root_raises_when_no_objective(tmp_path: Path):
    """No OBJECTIVE.md anywhere up from a temp dir → RuntimeError with a
    message that names the start path."""
    # Use a deeply nested path that won't bubble up into the real repo.
    # /private/tmp on macOS does not have OBJECTIVE.md as an ancestor.
    sub = tmp_path / "no_anchor_here"
    sub.mkdir()
    with pytest.raises(RuntimeError, match="could not locate the repo root"):
        _repo.find_repo_root(start=sub)


def test_ensure_build_imports_on_path_prepends_both_builds():
    repo_root = _repo.find_repo_root()
    returned = _repo.ensure_build_imports_on_path()
    assert returned == repo_root
    assert str(repo_root / "rag-app") in sys.path
    assert str(repo_root / "tool-use-agent") in sys.path


def test_ensure_build_imports_on_path_is_idempotent():
    """Re-running must not duplicate sys.path entries."""
    _repo.ensure_build_imports_on_path()
    before_rag = sys.path.count(str(_repo.find_repo_root() / "rag-app"))
    before_tua = sys.path.count(str(_repo.find_repo_root() / "tool-use-agent"))
    _repo.ensure_build_imports_on_path()
    _repo.ensure_build_imports_on_path()
    after_rag = sys.path.count(str(_repo.find_repo_root() / "rag-app"))
    after_tua = sys.path.count(str(_repo.find_repo_root() / "tool-use-agent"))
    assert after_rag == before_rag
    assert after_tua == before_tua


def test_ensure_build_imports_on_path_with_explicit_root(tmp_path: Path):
    """Callers can pass a precomputed repo_root to skip the walk."""
    fake_root = tmp_path
    (fake_root / "rag-app").mkdir()
    (fake_root / "tool-use-agent").mkdir()
    returned = _repo.ensure_build_imports_on_path(repo_root=fake_root)
    assert returned == fake_root
    assert str(fake_root / "rag-app") in sys.path
    assert str(fake_root / "tool-use-agent") in sys.path
