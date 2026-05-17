"""Tests for tool_use_agent.__main__: CLI dispatch (catalog / tool / ask).

Like rag-app/tests/test_main.py, this uses direct dispatch via argparse
Namespaces and ``contextlib.redirect_stdout`` rather than subprocess. The
live ``ask`` path is out of scope; only dry-run + JSON shape is exercised.
"""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from tool_use_agent.__main__ import (
    _agent_result_to_payload,
    _preview_output,
    _print_human,
    build_parser,
    cmd_ask,
    cmd_catalog,
    cmd_tool,
    main,
)
from tool_use_agent.agent import DEFAULT_MAX_STEPS, DEFAULT_MAX_TOKENS, DEFAULT_MODEL
from tool_use_agent.agent import build_dry_run_result
from tool_use_agent.trace import SCHEMA_VERSION


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*args, **kwargs)
    assert rc == 0
    return buf.getvalue()


def test_cmd_catalog_emits_eight_tools(monkeypatch):
    args = argparse.Namespace()
    stdout = _capture(cmd_catalog, args)
    payload = json.loads(stdout)
    assert isinstance(payload, list)
    assert len(payload) == 8
    names = [entry["name"] for entry in payload]
    assert names[0] == "list_repo_files"
    assert names[-1] == "file_rewrite"


def test_cmd_tool_dispatches_to_list_repo_files(monkeypatch, tiny_repo_root: Path):
    monkeypatch.chdir(tiny_repo_root)  # find_repo_root walks from package — but
    # the tool dispatcher hard-codes its repo_root to `find_repo_root(...)`
    # rooted at the installed package. The fixture cannot easily redirect
    # that. The simplest cross-cwd-independent check: set tool_name +
    # invoke; the dispatcher will walk to the actual repo's OBJECTIVE.md
    # and return its file list.
    args = argparse.Namespace(
        tool_name="list_repo_files",
        directory=".",
        pattern="*.md",
        json=True,
    )
    stdout = _capture(cmd_tool, args)
    payload = json.loads(stdout)
    assert isinstance(payload, list)


def test_cmd_tool_count_by_bucket_human_output(monkeypatch):
    args = argparse.Namespace(tool_name="count_by_bucket", json=False)
    stdout = _capture(cmd_tool, args)
    # Human output is "B1  <n>" style key-padded lines.
    assert "B1" in stdout
    assert "B2" in stdout
    assert "B3" in stdout


def test_cmd_ask_dry_run_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    args = argparse.Namespace(
        question="What is Acme?",
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        max_steps=DEFAULT_MAX_STEPS,
        dry_run=True,
        json=False,
    )
    stdout = _capture(cmd_ask, args)
    assert "Mode: dry-run" in stdout
    assert "Question: What is Acme?" in stdout
    assert "catalog (8 tools" in stdout


def test_cmd_ask_dry_run_json_shape(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    args = argparse.Namespace(
        question="Hello?",
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        max_steps=DEFAULT_MAX_STEPS,
        dry_run=True,
        json=True,
    )
    stdout = _capture(cmd_ask, args)
    payload = json.loads(stdout)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["mode"] == "dry-run"
    assert payload["question"] == "Hello?"
    assert payload["requested_model"] == DEFAULT_MODEL
    assert "record_id" in payload
    assert "corpus_fingerprint" in payload
    assert "generated_at" in payload
    assert payload["max_steps"] == DEFAULT_MAX_STEPS
    assert payload["steps_taken"] == 0
    assert payload["tool_calls"] == []


def test_cmd_ask_rejects_zero_max_steps(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    args = argparse.Namespace(
        question="Q?",
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        max_steps=0,
        dry_run=True,
        json=False,
    )
    rc = cmd_ask(args)
    assert rc == 2
    err = capsys.readouterr().err
    assert "--max-steps must be >= 1" in err


def test_cmd_ask_no_key_auto_falls_back_to_dry_run(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    args = argparse.Namespace(
        question="Q?",
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        max_steps=DEFAULT_MAX_STEPS,
        dry_run=False,
        json=False,
    )
    rc = cmd_ask(args)
    assert rc == 0
    captured = capsys.readouterr().out
    assert "falling back to dry-run" in captured
    assert "Mode: dry-run" in captured


def test_agent_result_to_payload_record_id_is_deterministic():
    result = build_dry_run_result("Q?", max_steps=4)
    a = _agent_result_to_payload(result, requested_model="m1")
    b = _agent_result_to_payload(result, requested_model="m1")
    assert a["record_id"] == b["record_id"]
    assert a["corpus_fingerprint"] == b["corpus_fingerprint"]


def test_agent_result_to_payload_record_id_changes_with_model():
    result = build_dry_run_result("Q?", max_steps=4)
    a = _agent_result_to_payload(result, requested_model="m1")
    b = _agent_result_to_payload(result, requested_model="m2")
    assert a["record_id"] != b["record_id"]


def test_main_no_args_errors():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_main_help_exits_clean(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "catalog" in out
    assert "tool" in out
    assert "ask" in out


def test_main_catalog_dispatch(capsys):
    rc = main(["catalog"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 8


def test_main_ask_dry_run_dispatch(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rc = main(["ask", "Hello?", "--dry-run", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "dry-run"
    assert payload["question"] == "Hello?"


def test_build_parser_subcommand_names():
    parser = build_parser()
    actions = {a.dest: a for a in parser._actions}
    # The top-level parser has a 'command' subparsers action.
    assert "command" in actions


def test_print_human_string_passthrough(capsys):
    _print_human("read_repo_file", "hello world")
    assert capsys.readouterr().out == "hello world\n"


def test_print_human_empty_list_shows_marker(capsys):
    _print_human("list_repo_files", [])
    assert "(no results from list_repo_files)" in capsys.readouterr().out


def test_print_human_list_of_strings_one_per_line(capsys):
    _print_human("list_repo_files", ["a.md", "b.md"])
    out = capsys.readouterr().out
    assert out == "a.md\nb.md\n"


def test_print_human_list_of_dicts_pipe_format(capsys):
    _print_human("grep_repo", [{"path": "x", "line_number": 1, "line": "y"}])
    out = capsys.readouterr().out
    assert "path=" in out
    assert "|" in out


def test_print_human_dict_key_padded(capsys):
    _print_human("count_by_bucket", {"B1": 0, "B2": 1, "B3": 2})
    out = capsys.readouterr().out
    assert "B1" in out and "B2" in out and "B3" in out


def test_print_human_falls_back_to_json(capsys):
    # An int (non-list, non-dict, non-str) falls to the JSON dump branch.
    _print_human("count_by_bucket", 42)
    out = capsys.readouterr().out
    assert "42" in out


def test_preview_output_truncates_long_strings():
    long = "x" * 500
    out = _preview_output(long, limit=50)
    assert len(out) == 50
    assert out.endswith("...")


def test_preview_output_handles_non_string():
    out = _preview_output([{"k": "v"}])
    assert "k" in out and "v" in out


def test_preview_output_replaces_newlines():
    out = _preview_output("a\nb\nc")
    assert "\n" not in out
