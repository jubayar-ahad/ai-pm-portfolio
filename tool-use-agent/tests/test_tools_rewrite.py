"""Tests for tool_use_agent.tools_rewrite.file_rewrite.

The tool's safety lock is two layers: a static operation enum
(replace/append/prepend) and a sandbox-root resolve that refuses any
path resolving outside `tool-use-agent/sandbox/`. Both layers are pinned
independently so a regression in either is loud.

Each test stages its own sandbox tree under `tmp_path` and runs the
tool against that tree, never the committed `tool-use-agent/sandbox/`
seed — so the seed files stay byte-identical for the agent's demo and
the suite is hermetic with no cleanup teardown beyond pytest's tmp_path.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tool_use_agent.tools_rewrite import (
    MAX_CONTENT_BYTES,
    MAX_FILE_BYTES,
    OPERATIONS,
    SANDBOX_RELDIR,
    file_rewrite,
)


# --------------------------------------------------------------------------- #
# Helpers — stage an isolated sandbox tree under tmp_path.
# --------------------------------------------------------------------------- #


def _make_sandbox(tmp_path: Path, files: dict[str, str]) -> Path:
    """Build a `repo_root` under tmp_path with a populated sandbox tree."""
    repo_root = tmp_path / "repo"
    sandbox = repo_root / SANDBOX_RELDIR
    sandbox.mkdir(parents=True, exist_ok=True)
    for relpath, content in files.items():
        full = sandbox / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    return repo_root


# --------------------------------------------------------------------------- #
# Module-level constants are part of the public contract.
# --------------------------------------------------------------------------- #


def test_operations_set_is_exactly_three():
    assert OPERATIONS == frozenset({"replace", "append", "prepend"})


def test_sandbox_reldir_is_tool_use_agent_sandbox():
    assert SANDBOX_RELDIR == "tool-use-agent/sandbox"


def test_max_caps_are_one_megabyte():
    assert MAX_FILE_BYTES == 1_000_000
    assert MAX_CONTENT_BYTES == 1_000_000


# --------------------------------------------------------------------------- #
# Happy path — each operation against an existing file.
# --------------------------------------------------------------------------- #


def test_replace_overwrites_existing_file(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "original content\n"})
    result = file_rewrite(repo_root, "notes.md", "replace", "brand new\n")
    assert isinstance(result, dict)
    assert result["path"] == "notes.md"
    assert result["operation"] == "replace"
    assert result["bytes_before"] == len("original content\n".encode("utf-8"))
    assert result["bytes_after"] == len("brand new\n".encode("utf-8"))
    assert "-original content" in result["diff"]
    assert "+brand new" in result["diff"]
    on_disk = (repo_root / SANDBOX_RELDIR / "notes.md").read_text("utf-8")
    assert on_disk == "brand new\n"


def test_append_adds_suffix_to_existing_content(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "head\n"})
    result = file_rewrite(repo_root, "notes.md", "append", "tail\n")
    assert isinstance(result, dict)
    assert result["operation"] == "append"
    on_disk = (repo_root / SANDBOX_RELDIR / "notes.md").read_text("utf-8")
    assert on_disk == "head\ntail\n"
    assert result["bytes_before"] == 5
    assert result["bytes_after"] == 10


def test_prepend_adds_prefix_before_existing_content(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "tail\n"})
    result = file_rewrite(repo_root, "notes.md", "prepend", "head\n")
    assert isinstance(result, dict)
    assert result["operation"] == "prepend"
    on_disk = (repo_root / SANDBOX_RELDIR / "notes.md").read_text("utf-8")
    assert on_disk == "head\ntail\n"


def test_replace_with_identical_content_emits_empty_diff(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "same\n"})
    result = file_rewrite(repo_root, "notes.md", "replace", "same\n")
    assert isinstance(result, dict)
    # No textual change → unified_diff produces no hunks.
    assert result["diff"] == ""
    assert result["bytes_before"] == result["bytes_after"]


def test_diff_contains_unified_headers_with_a_b_prefixes(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "one\n"})
    result = file_rewrite(repo_root, "notes.md", "replace", "two\n")
    assert "--- a/notes.md" in result["diff"]
    assert "+++ b/notes.md" in result["diff"]


def test_nested_path_under_sandbox_is_allowed(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"deep/inner/buf.md": "x\n"})
    result = file_rewrite(repo_root, "deep/inner/buf.md", "append", "y\n")
    assert isinstance(result, dict)
    on_disk = (
        repo_root / SANDBOX_RELDIR / "deep" / "inner" / "buf.md"
    ).read_text("utf-8")
    assert on_disk == "x\ny\n"


# --------------------------------------------------------------------------- #
# Sandbox-escape layer — the second layer of the guardrail.
# --------------------------------------------------------------------------- #


def test_parent_traversal_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    # Stage a sibling file outside the sandbox that the traversal would
    # otherwise target.
    outside = repo_root / "outside.md"
    outside.write_text("original\n", encoding="utf-8")
    result = file_rewrite(repo_root, "../outside.md", "replace", "hijacked\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
    assert "escapes the sandbox root" in result
    # The outside file must NOT have been touched.
    assert outside.read_text("utf-8") == "original\n"


def test_absolute_path_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    # An absolute path joined with the sandbox root resolves to the
    # absolute path itself — Path("/foo") / "/etc" == Path("/etc") on
    # POSIX — so we expect a clean refusal.
    outside = tmp_path / "elsewhere.md"
    outside.write_text("untouched\n", encoding="utf-8")
    result = file_rewrite(repo_root, str(outside), "replace", "no\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
    assert outside.read_text("utf-8") == "untouched\n"


def test_symlink_pointing_outside_sandbox_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    target = repo_root / "outside.md"
    target.write_text("original\n", encoding="utf-8")
    link = repo_root / SANDBOX_RELDIR / "shortcut.md"
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    result = file_rewrite(repo_root, "shortcut.md", "replace", "hijacked\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
    assert "escapes the sandbox root" in result
    assert target.read_text("utf-8") == "original\n"


def test_path_equal_to_sandbox_root_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    result = file_rewrite(repo_root, ".", "replace", "no\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR:")


# --------------------------------------------------------------------------- #
# Operation-enum layer — the first layer of the guardrail.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad_op",
    [
        "delete",
        "DELETE",
        "Replace",  # case-sensitive enum (no folding)
        "patch",
        "rm",
        "",
        " ",
    ],
)
def test_unknown_operation_is_refused(tmp_path: Path, bad_op: str):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    result = file_rewrite(repo_root, "notes.md", bad_op, "content\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR: unknown operation")
    # And the file must not have been touched.
    assert (repo_root / SANDBOX_RELDIR / "notes.md").read_text("utf-8") == "x\n"


# --------------------------------------------------------------------------- #
# Existence and shape — refusal contract.
# --------------------------------------------------------------------------- #


def test_missing_file_is_refused_even_for_replace(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {})  # empty sandbox
    result = file_rewrite(repo_root, "nope.md", "replace", "content\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR: no such file in sandbox")
    assert not (repo_root / SANDBOX_RELDIR / "nope.md").exists()


def test_missing_file_refused_for_append_and_prepend(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {})
    for op in ("append", "prepend"):
        result = file_rewrite(repo_root, "nope.md", op, "content\n")
        assert isinstance(result, str)
        assert result.startswith("ERROR: no such file in sandbox")


def test_directory_target_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"sub/file.md": "x\n"})
    result = file_rewrite(repo_root, "sub", "replace", "no\n")
    assert isinstance(result, str)
    assert "not a regular file" in result or "escapes" in result


def test_empty_path_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    result = file_rewrite(repo_root, "", "replace", "no\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR: empty path")


def test_non_string_content_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    result = file_rewrite(repo_root, "notes.md", "replace", 12345)  # type: ignore[arg-type]
    assert isinstance(result, str)
    assert result.startswith("ERROR: content must be a string")


def test_non_utf8_existing_file_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {})
    binary = repo_root / SANDBOX_RELDIR / "blob.bin"
    binary.write_bytes(b"\xff\xfe\x00\x01")
    result = file_rewrite(repo_root, "blob.bin", "append", "tail\n")
    assert isinstance(result, str)
    assert "cannot decode" in result


# --------------------------------------------------------------------------- #
# Size caps.
# --------------------------------------------------------------------------- #


def test_content_over_cap_is_refused(tmp_path: Path):
    repo_root = _make_sandbox(tmp_path, {"notes.md": "x\n"})
    big = "a" * (MAX_CONTENT_BYTES + 1)
    result = file_rewrite(repo_root, "notes.md", "replace", big)
    assert isinstance(result, str)
    assert "exceeds" in result
    assert "content" in result
    # File untouched.
    assert (repo_root / SANDBOX_RELDIR / "notes.md").read_text("utf-8") == "x\n"


def test_post_edit_file_over_cap_is_refused(tmp_path: Path):
    # Start with a near-cap file, then append small content that pushes
    # past the cap. The content itself is under the content cap so this
    # exercises the *post-edit* size check distinctly.
    repo_root = _make_sandbox(
        tmp_path,
        {"big.md": "a" * (MAX_FILE_BYTES - 10)},
    )
    payload = "b" * 100  # under MAX_CONTENT_BYTES, but total > MAX_FILE_BYTES
    result = file_rewrite(repo_root, "big.md", "append", payload)
    assert isinstance(result, str)
    assert "post-edit file size" in result
    # File untouched.
    on_disk = (repo_root / SANDBOX_RELDIR / "big.md").read_text("utf-8")
    assert len(on_disk) == MAX_FILE_BYTES - 10


# --------------------------------------------------------------------------- #
# Sandbox auto-create — defensive lazy mkdir.
# --------------------------------------------------------------------------- #


def test_sandbox_root_is_created_if_missing(tmp_path: Path):
    repo_root = tmp_path / "fresh-repo"
    repo_root.mkdir()
    # Sandbox does not exist; first tool call should mkdir it then
    # refuse the file as missing (not crash).
    result = file_rewrite(repo_root, "nope.md", "replace", "content\n")
    assert isinstance(result, str)
    assert result.startswith("ERROR: no such file in sandbox")
    assert (repo_root / SANDBOX_RELDIR).is_dir()
