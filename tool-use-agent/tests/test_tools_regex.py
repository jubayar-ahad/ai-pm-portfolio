"""Tests for tool_use_agent.tools_regex.regex_extract.

The tool's safety lock is two layers: ``re.compile`` plus a pattern-length
cap (Layer 1) and ``_resolve_inside_repo`` plus a match-count ceiling
(Layer 2). Both layers are pinned independently so a regression in either
is loud.

Tests run against the committed ``tests/fixtures/tiny_repo/`` tree
(read-only) and against tmp_path-staged trees for the path-resolution
and size-cap surfaces.
"""

from __future__ import annotations

from pathlib import Path


from tool_use_agent.tools_regex import (
    MATCH_CEILING,
    MAX_PATTERN_LENGTH,
    regex_extract,
)
from tool_use_agent.tools_repo import MAX_GREP_FILE_BYTES


# --------------------------------------------------------------------------- #
# Module-level constants are part of the public contract.
# --------------------------------------------------------------------------- #


def test_max_pattern_length_is_one_thousand():
    assert MAX_PATTERN_LENGTH == 1000


def test_match_ceiling_is_one_thousand():
    assert MATCH_CEILING == 1000


# --------------------------------------------------------------------------- #
# Happy path — pattern matching against the tiny_repo fixture.
# --------------------------------------------------------------------------- #


def test_extract_matches_in_a_single_file(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"Pangolin\w*", path="animals.md")
    assert isinstance(result, dict)
    assert result["pattern"] == r"Pangolin\w*"
    assert result["path"] == "animals.md"
    assert result["match_count"] == 1
    assert result["truncated"] is False
    match = result["matches"][0]
    assert match["path"] == "animals.md"
    assert match["match"] == "Pangolins"
    assert match["line_number"] == 3
    assert match["groups"] == []


def test_extract_returns_capture_groups(tiny_repo_root: Path):
    # Capture: (city) is the (capital|imperial capital) of (country)
    result = regex_extract(
        tiny_repo_root,
        r"(\w+) is the capital of (\w+)",
        path="sub/cities.md",
    )
    assert isinstance(result, dict)
    assert result["match_count"] == 1
    match = result["matches"][0]
    assert match["groups"] == ["Reykjavik", "Iceland"]
    assert match["match"] == "Reykjavik is the capital of Iceland"


def test_extract_walks_directory_tree(tiny_repo_root: Path):
    # Match "capital" anywhere — should hit both sub/cities.md lines and
    # not the animals.md file.
    result = regex_extract(tiny_repo_root, r"capital", path=".")
    assert isinstance(result, dict)
    paths_hit = {m["path"] for m in result["matches"]}
    assert "sub/cities.md" in paths_hit
    assert "animals.md" not in paths_hit


def test_extract_returns_span_as_two_ints(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"Pangolin", path="animals.md")
    match = result["matches"][0]
    span = match["span"]
    assert isinstance(span, list)
    assert len(span) == 2
    assert span[0] < span[1]


def test_inline_case_insensitive_flag_works(tiny_repo_root: Path):
    # The pattern itself carries `(?i)` — the tool exposes no flags arg.
    result = regex_extract(tiny_repo_root, r"(?i)PANGOLIN", path="animals.md")
    assert isinstance(result, dict)
    assert result["match_count"] == 1
    assert result["matches"][0]["match"] == "Pangolin"


def test_multiple_matches_on_one_line(tmp_path: Path):
    repo_root = _make_repo(tmp_path, {"buf.md": "abc abc abc\n"})
    result = regex_extract(repo_root, r"abc", path="buf.md")
    assert isinstance(result, dict)
    assert result["match_count"] == 3
    line_numbers = {m["line_number"] for m in result["matches"]}
    assert line_numbers == {1}


def test_max_matches_caps_results(tmp_path: Path):
    repo_root = _make_repo(tmp_path, {"buf.md": "abc abc abc abc abc\n"})
    result = regex_extract(repo_root, r"abc", path="buf.md", max_matches=2)
    assert isinstance(result, dict)
    assert result["match_count"] == 2
    assert result["truncated"] is True


def test_no_matches_returns_empty_match_list(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"zzz_no_match_zzz")
    assert isinstance(result, dict)
    assert result["matches"] == []
    assert result["match_count"] == 0
    assert result["truncated"] is False


def test_path_defaults_to_repo_root(tiny_repo_root: Path):
    # No path arg → defaults to "." → walks tiny_repo.
    result = regex_extract(tiny_repo_root, r"axolotl")
    assert isinstance(result, dict)
    assert result["match_count"] == 1
    assert result["matches"][0]["path"] == "animals.md"


# --------------------------------------------------------------------------- #
# Layer 1 — regex compile + pattern length cap.
# --------------------------------------------------------------------------- #


def test_malformed_regex_is_refused(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"(unclosed group")
    assert isinstance(result, str)
    assert result.startswith("ERROR: invalid regex")


def test_empty_pattern_is_refused(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, "")
    assert isinstance(result, str)
    assert result.startswith("ERROR: empty pattern")


def test_pattern_length_cap_is_enforced(tiny_repo_root: Path):
    huge = "a" * (MAX_PATTERN_LENGTH + 1)
    result = regex_extract(tiny_repo_root, huge)
    assert isinstance(result, str)
    assert "pattern length" in result
    assert str(MAX_PATTERN_LENGTH) in result


def test_pattern_exactly_at_length_cap_is_allowed(tiny_repo_root: Path):
    # No regex metachars — just a literal of cap-length. Should compile
    # and search without error (likely zero matches).
    pattern = "z" * MAX_PATTERN_LENGTH
    result = regex_extract(tiny_repo_root, pattern)
    assert isinstance(result, dict)
    assert result["match_count"] == 0


# --------------------------------------------------------------------------- #
# Layer 2 — repo-root resolve + match-count ceiling.
# --------------------------------------------------------------------------- #


def test_path_escape_is_refused(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"x", path="../../../etc/passwd")
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
    assert "escapes the repo root" in result


def test_missing_path_returns_error(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"x", path="does/not/exist.md")
    assert isinstance(result, str)
    assert result.startswith("ERROR: no such path")


def test_max_matches_zero_is_refused(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"x", max_matches=0)
    assert isinstance(result, str)
    assert result.startswith("ERROR: max_matches")


def test_max_matches_over_ceiling_is_refused(tiny_repo_root: Path):
    result = regex_extract(
        tiny_repo_root, r"x", max_matches=MATCH_CEILING + 1
    )
    assert isinstance(result, str)
    assert "hard ceiling" in result
    assert str(MATCH_CEILING) in result


# --------------------------------------------------------------------------- #
# Non-text + size-cap surfaces.
# --------------------------------------------------------------------------- #


def _make_repo(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    """Build a tmp_path repo (OBJECTIVE.md anchor + given files)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "OBJECTIVE.md").write_text("stub", encoding="utf-8")
    for relpath, content in files.items():
        full = repo / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            full.write_bytes(content)
        else:
            full.write_text(content, encoding="utf-8")
    return repo


def test_non_text_suffix_is_skipped(tmp_path: Path):
    # A `.png` file containing matchable text should be skipped because
    # the suffix is not in TEXT_SUFFIXES.
    repo_root = _make_repo(tmp_path, {"image.png": "secret-token-12345\n"})
    result = regex_extract(repo_root, r"secret-token-\d+", path=".")
    assert isinstance(result, dict)
    assert result["match_count"] == 0


def test_excluded_directory_is_skipped(tmp_path: Path):
    # A `.git/config` file containing matchable text should be skipped.
    repo_root = _make_repo(
        tmp_path,
        {".git/config.md": "secret-token-12345\n", "real.md": "real\n"},
    )
    result = regex_extract(repo_root, r"secret-token-\d+", path=".")
    assert isinstance(result, dict)
    assert result["match_count"] == 0


def test_oversize_file_is_skipped(tmp_path: Path):
    # File over MAX_GREP_FILE_BYTES is skipped silently.
    repo_root = _make_repo(
        tmp_path, {"big.md": "match\n" + "x" * (MAX_GREP_FILE_BYTES + 1)}
    )
    result = regex_extract(repo_root, r"match", path="big.md")
    # The file IS the target path; oversize means it just yields no matches.
    assert isinstance(result, dict)
    assert result["match_count"] == 0


def test_binary_file_with_text_suffix_yields_no_matches(tmp_path: Path):
    # A `.md` file with un-decodable bytes is skipped by the
    # UnicodeDecodeError catch.
    repo_root = _make_repo(tmp_path, {"blob.md": b"\xff\xfe\x00\x01"})
    result = regex_extract(repo_root, r".", path="blob.md")
    assert isinstance(result, dict)
    assert result["match_count"] == 0


# --------------------------------------------------------------------------- #
# Single-file vs directory targeting.
# --------------------------------------------------------------------------- #


def test_targeting_a_subdirectory_scopes_search(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"\w+", path="sub", max_matches=50)
    paths_hit = {m["path"] for m in result["matches"]}
    # Every match must be in the sub/ tree.
    assert paths_hit
    for p in paths_hit:
        assert p.startswith("sub/")


def test_targeting_a_single_file_skips_directory_walk(tiny_repo_root: Path):
    # When the path is a file, candidates is just that file.
    result = regex_extract(
        tiny_repo_root, r"capital", path="sub/cities.md"
    )
    paths_hit = {m["path"] for m in result["matches"]}
    assert paths_hit == {"sub/cities.md"}


# --------------------------------------------------------------------------- #
# Echo invariants — pattern and path are preserved byte-for-byte in the
# response so the agent can correlate request and response.
# --------------------------------------------------------------------------- #


def test_pattern_and_path_are_echoed_in_response(tiny_repo_root: Path):
    pattern = r"(?P<animal>Pangolin)"
    path = "animals.md"
    result = regex_extract(tiny_repo_root, pattern, path=path)
    assert result["pattern"] == pattern
    assert result["path"] == path


def test_truncated_flag_false_when_under_cap(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, r"Pangolin", path="animals.md")
    assert result["truncated"] is False


# --------------------------------------------------------------------------- #
# Type-validation surface — empty / wrong-type pattern.
# --------------------------------------------------------------------------- #


def test_non_string_pattern_is_refused(tiny_repo_root: Path):
    result = regex_extract(tiny_repo_root, 12345)  # type: ignore[arg-type]
    assert isinstance(result, str)
    assert result.startswith("ERROR: empty pattern")
