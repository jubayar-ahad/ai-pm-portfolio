"""Tests for tool_use_agent.tools_repo: list/read/grep + repo-root anchor."""

from __future__ import annotations

from pathlib import Path

import pytest

from tool_use_agent.tools_repo import (
    EXCLUDED_DIR_NAMES,
    GrepMatch,
    find_repo_root,
    grep_repo,
    list_repo_files,
    read_repo_file,
)


def test_find_repo_root_locates_anchor(tiny_repo_root: Path):
    nested = tiny_repo_root / "sub"
    assert find_repo_root(nested) == tiny_repo_root
    assert find_repo_root(tiny_repo_root) == tiny_repo_root


def test_find_repo_root_raises_when_anchor_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        find_repo_root(tmp_path)


def test_list_repo_files_default_pattern_finds_markdown(tiny_repo_root: Path):
    files = list_repo_files(tiny_repo_root)
    # animals.md at the root + sub/cities.md + OBJECTIVE.md +
    # templates/INTERVIEW_TRACKER.md
    assert "animals.md" in files
    assert "sub/cities.md" in files
    assert "OBJECTIVE.md" in files
    assert "templates/INTERVIEW_TRACKER.md" in files


def test_list_repo_files_returns_sorted_unique_paths(tiny_repo_root: Path):
    files = list_repo_files(tiny_repo_root)
    assert files == sorted(files)
    assert len(files) == len(set(files))


def test_list_repo_files_directory_filter(tiny_repo_root: Path):
    files = list_repo_files(tiny_repo_root, directory="sub")
    assert files == ["sub/cities.md"]


def test_list_repo_files_excludes_well_known_dirs(tiny_repo_root: Path, tmp_path: Path):
    # Materialize a copy with a .git subdirectory the function must skip.
    copy_root = tmp_path / "repo"
    copy_root.mkdir()
    (copy_root / "OBJECTIVE.md").write_text("stub", encoding="utf-8")
    (copy_root / "real.md").write_text("# real\n", encoding="utf-8")
    git_dir = copy_root / ".git"
    git_dir.mkdir()
    (git_dir / "config.md").write_text("# hidden\n", encoding="utf-8")
    pycache_dir = copy_root / "src" / "__pycache__"
    pycache_dir.mkdir(parents=True)
    (pycache_dir / "x.md").write_text("# more hidden\n", encoding="utf-8")
    files = list_repo_files(copy_root)
    assert "real.md" in files
    for excluded in EXCLUDED_DIR_NAMES:
        assert not any(excluded in path.split("/") for path in files), files


def test_list_repo_files_empty_on_missing_directory(tiny_repo_root: Path):
    assert list_repo_files(tiny_repo_root, directory="does/not/exist") == []


def test_list_repo_files_explicit_doublestar_pattern(tiny_repo_root: Path):
    files = list_repo_files(tiny_repo_root, pattern="**/*.md")
    assert "animals.md" in files
    assert "sub/cities.md" in files


def test_read_repo_file_full_file(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "animals.md")
    assert "Pangolins" in out
    assert "axolotl" in out


def test_read_repo_file_line_range(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "animals.md", start_line=3, end_line=3)
    assert "Pangolins" in out
    assert "Octopuses" not in out


def test_read_repo_file_open_ended_range(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "animals.md", start_line=5)
    # Line 5 = Octopus paragraph onward
    assert "Octopuses" in out
    assert "axolotl" in out
    assert "Pangolins" not in out


def test_read_repo_file_missing_returns_error_string(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "nope.md")
    assert out.startswith("ERROR:")
    assert "no such file" in out


def test_read_repo_file_directory_returns_error(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "sub")
    assert out.startswith("ERROR:")
    assert "not a regular file" in out


def test_read_repo_file_path_escape_returns_error(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "../../../etc/passwd")
    assert out.startswith("ERROR:")
    assert "escapes the repo root" in out


def test_read_repo_file_bad_start_line_returns_error(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "animals.md", start_line=0)
    assert out.startswith("ERROR:")
    assert "start_line" in out


def test_read_repo_file_end_before_start_returns_error(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "animals.md", start_line=5, end_line=3)
    assert out.startswith("ERROR:")
    assert "end_line" in out


def test_read_repo_file_start_past_eof_returns_error(tiny_repo_root: Path):
    out = read_repo_file(tiny_repo_root, "animals.md", start_line=999)
    assert out.startswith("ERROR:")
    assert "file length" in out


def test_grep_repo_finds_substring(tiny_repo_root: Path):
    matches = grep_repo(tiny_repo_root, query="Pangolin")
    assert matches
    assert isinstance(matches[0], GrepMatch)
    assert matches[0].path == "animals.md"
    assert "Pangolin" in matches[0].line


def test_grep_repo_is_case_insensitive(tiny_repo_root: Path):
    matches = grep_repo(tiny_repo_root, query="PANGOLIN")
    assert matches
    assert "Pangolin" in matches[0].line


def test_grep_repo_respects_max_matches(tiny_repo_root: Path):
    matches = grep_repo(tiny_repo_root, query="the", max_matches=2)
    assert len(matches) == 2


def test_grep_repo_empty_query_returns_empty(tiny_repo_root: Path):
    assert grep_repo(tiny_repo_root, query="") == []


def test_grep_repo_max_matches_zero_returns_empty(tiny_repo_root: Path):
    assert grep_repo(tiny_repo_root, query="the", max_matches=0) == []


def test_grep_repo_missing_path_returns_empty(tiny_repo_root: Path):
    assert grep_repo(tiny_repo_root, query="x", path="not/there") == []


def test_grep_repo_targets_specific_file(tiny_repo_root: Path):
    matches = grep_repo(tiny_repo_root, query="capital", path="sub/cities.md")
    assert matches
    for m in matches:
        assert m.path == "sub/cities.md"
