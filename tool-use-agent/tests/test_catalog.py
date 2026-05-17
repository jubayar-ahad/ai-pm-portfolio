"""Tests for tool_use_agent.catalog: registration, JSON schemas, dispatch."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from tool_use_agent.catalog import (
    CATALOG,
    Tool,
    _serialize,
    build_catalog,
    call_tool,
    catalog_as_anthropic_tools,
)
from tool_use_agent.tools_pipeline import ALL_STAGES, BUCKETS
from tool_use_agent.tools_rewrite import OPERATIONS as REWRITE_OPERATIONS

BUILD_ROOT = Path(__file__).parent.parent
REPO_ROOT = BUILD_ROOT.parent

EXPECTED_TOOL_NAMES: tuple[str, ...] = (
    "list_repo_files",
    "read_repo_file",
    "grep_repo",
    "list_pipeline_rows",
    "count_by_stage",
    "count_by_bucket",
    "sql_query",
    "file_rewrite",
    "regex_extract",
)


def test_catalog_has_nine_tools_in_locked_order():
    assert list(CATALOG.keys()) == list(EXPECTED_TOOL_NAMES)


def test_catalog_names_are_unique():
    names = list(CATALOG.keys())
    assert len(names) == len(set(names))


def test_build_catalog_returns_fresh_dict_each_call():
    first = build_catalog()
    second = build_catalog()
    assert list(first.keys()) == list(second.keys())
    assert first is not second


def test_every_tool_has_required_fields():
    for name, tool in CATALOG.items():
        assert isinstance(tool, Tool)
        assert tool.name == name
        assert tool.description.strip() != ""
        assert callable(tool.impl)
        assert isinstance(tool.input_schema, dict)


def test_every_tool_schema_is_an_object_with_additional_properties_false():
    for tool in CATALOG.values():
        schema = tool.input_schema
        assert schema.get("type") == "object"
        assert schema.get("additionalProperties") is False
        assert "properties" in schema


def test_required_fields_are_subset_of_properties():
    for tool in CATALOG.values():
        properties = tool.input_schema.get("properties", {})
        required = tool.input_schema.get("required", [])
        assert set(required).issubset(set(properties.keys()))


def test_list_pipeline_rows_enum_matches_locked_vocab():
    schema = CATALOG["list_pipeline_rows"].input_schema
    stage_enum = schema["properties"]["stage"]["enum"]
    bucket_enum = schema["properties"]["bucket"]["enum"]
    assert set(stage_enum) == set(list(ALL_STAGES) + [None])
    assert set(bucket_enum) == set(list(BUCKETS) + [None])


def test_serialize_handles_dataclasses():
    @dataclass(frozen=True)
    class Box:
        x: int
        y: str

    out = _serialize(Box(1, "two"))
    assert out == {"x": 1, "y": "two"}


def test_serialize_recurses_into_lists_tuples_dicts():
    @dataclass(frozen=True)
    class Box:
        x: int

    out = _serialize([Box(1), (Box(2),), {"k": Box(3)}])
    assert out == [{"x": 1}, [{"x": 2}], {"k": {"x": 3}}]


def test_serialize_passes_through_scalars():
    assert _serialize(5) == 5
    assert _serialize("s") == "s"
    assert _serialize(None) is None
    assert _serialize(True) is True


def test_call_tool_dispatches_by_name(tiny_repo_root: Path):
    result = call_tool("list_repo_files", tiny_repo_root, pattern="*.md")
    assert isinstance(result, list)
    assert "animals.md" in result


def test_call_tool_unknown_name_raises_keyerror(tiny_repo_root: Path):
    with pytest.raises(KeyError):
        call_tool("nonexistent_tool", tiny_repo_root)


def test_call_tool_serializes_dataclass_results(tiny_repo_root: Path):
    matches = call_tool("grep_repo", tiny_repo_root, query="Pangolin")
    assert isinstance(matches, list)
    assert matches
    assert isinstance(matches[0], dict)
    assert set(matches[0].keys()) == {"path", "line_number", "line"}


def test_catalog_as_anthropic_tools_shape_matches_sdk_contract():
    payload = catalog_as_anthropic_tools()
    assert isinstance(payload, list)
    assert len(payload) == len(CATALOG)
    for entry in payload:
        assert set(entry.keys()) == {"name", "description", "input_schema"}


def test_catalog_as_anthropic_tools_preserves_order():
    payload = catalog_as_anthropic_tools()
    names = [entry["name"] for entry in payload]
    assert names == list(EXPECTED_TOOL_NAMES)


def test_catalog_as_anthropic_tools_is_json_serializable():
    payload = catalog_as_anthropic_tools()
    # Should not raise — Anthropic SDK serializes this for the wire.
    json.dumps(payload, sort_keys=True, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Per-tool schema-shape tests for the three new tools (NEXT_WORK item 6
# sub-checkbox 4). These pin the catalog-level contract — required fields,
# enum vocab, default values, integer bounds, and the safety-relevant
# description hints — so the three new tools cannot drift from their
# locked schemas without a test failure at the catalog boundary.


def test_sql_query_schema_shape():
    schema = CATALOG["sql_query"].input_schema
    properties = schema["properties"]
    assert set(properties.keys()) == {"path", "sql", "max_rows"}
    assert set(schema["required"]) == {"path", "sql"}
    assert properties["path"]["type"] == "string"
    assert properties["sql"]["type"] == "string"
    assert properties["max_rows"]["type"] == "integer"
    assert properties["max_rows"]["minimum"] == 1
    assert properties["max_rows"]["default"] == 100


def test_sql_query_description_pins_read_only_layers():
    description = CATALOG["sql_query"].description.lower()
    # Both safety layers (denylist + mode=ro) must be advertised so the
    # model sees the read-only contract in its tool catalog prompt.
    assert "read-only" in description
    assert "mode=ro" in description
    assert "rejected" in description


def test_file_rewrite_schema_shape():
    schema = CATALOG["file_rewrite"].input_schema
    properties = schema["properties"]
    assert set(properties.keys()) == {"path", "operation", "content"}
    assert set(schema["required"]) == {"path", "operation", "content"}
    assert properties["path"]["type"] == "string"
    assert properties["operation"]["type"] == "string"
    assert properties["content"]["type"] == "string"


def test_file_rewrite_operation_enum_matches_locked_vocab():
    # The operation enum must mirror tools_rewrite.OPERATIONS exactly —
    # the catalog is the single source of truth the live agent loop sees.
    schema = CATALOG["file_rewrite"].input_schema
    operation_enum = schema["properties"]["operation"]["enum"]
    assert set(operation_enum) == set(REWRITE_OPERATIONS)
    # Enum is rendered sorted for deterministic schema serialization.
    assert operation_enum == sorted(operation_enum)


def test_file_rewrite_description_pins_sandbox_contract():
    description = CATALOG["file_rewrite"].description.lower()
    # The sandbox-only property is the safety contract the model must see.
    assert "sandbox" in description
    assert "refused" in description or "refuse" in description


def test_regex_extract_schema_shape():
    schema = CATALOG["regex_extract"].input_schema
    properties = schema["properties"]
    assert set(properties.keys()) == {"pattern", "path", "max_matches"}
    # Only `pattern` is required — path defaults to '.' and max_matches to 20.
    assert set(schema["required"]) == {"pattern"}
    assert properties["pattern"]["type"] == "string"
    assert properties["path"]["type"] == "string"
    assert properties["path"]["default"] == "."
    assert properties["max_matches"]["type"] == "integer"
    assert properties["max_matches"]["minimum"] == 1
    assert properties["max_matches"]["default"] == 20


def test_regex_extract_description_pins_read_only_and_compile_first():
    description = CATALOG["regex_extract"].description.lower()
    # Read-only is a baseline property; the model also needs to know the
    # pattern is compiled (so it knows to refine on a re.error refusal).
    assert "read-only" in description
    assert "regex" in description


# ---------------------------------------------------------------------------
# Catalog-level dispatch tests for the three new tools. Each test routes
# through `call_tool` (not the tool's impl) so the wiring — name lookup,
# kwarg pass-through, dataclass serialization, and the live `CATALOG`
# binding — is exercised end-to-end at the dispatcher boundary.


def test_call_tool_dispatches_sql_query_against_fixture_db():
    # Repo-relative path to the build-root sample.db fixture; the sql_query
    # tool resolves against `repo_root` (here, the real repo root).
    result = call_tool(
        "sql_query",
        REPO_ROOT,
        path="tool-use-agent/fixtures/sample.db",
        sql="SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        max_rows=10,
    )
    assert isinstance(result, dict)
    assert set(result.keys()) == {"columns", "rows", "row_count"}
    table_names = {row["name"] for row in result["rows"]}
    assert {"authors", "books", "book_genres"}.issubset(table_names)


def test_call_tool_sql_query_refuses_write_keyword():
    # The static denylist must fire BEFORE the file is even opened — passing
    # a non-existent path proves the order: the keyword refusal precedes
    # the missing-file refusal.
    result = call_tool(
        "sql_query",
        REPO_ROOT,
        path="tool-use-agent/fixtures/does-not-exist.db",
        sql="DELETE FROM books",
    )
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
    assert "DELETE" in result


def test_call_tool_dispatches_file_rewrite_against_sandbox(tmp_path: Path):
    # Stage a throwaway sandbox so the dispatch test doesn't touch the
    # committed sandbox/notes.md under git. `repo_root` is `tmp_path` and
    # the tool creates `tmp_path/tool-use-agent/sandbox/` lazily.
    sandbox = tmp_path / "tool-use-agent" / "sandbox"
    sandbox.mkdir(parents=True)
    (sandbox / "scratch.md").write_text("seed\n", encoding="utf-8")

    result = call_tool(
        "file_rewrite",
        tmp_path,
        path="scratch.md",
        operation="append",
        content="appended\n",
    )
    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "path",
        "operation",
        "bytes_before",
        "bytes_after",
        "diff",
    }
    assert result["operation"] == "append"
    assert result["bytes_after"] > result["bytes_before"]
    assert (sandbox / "scratch.md").read_text(encoding="utf-8") == (
        "seed\nappended\n"
    )


def test_call_tool_file_rewrite_refuses_sandbox_escape(tmp_path: Path):
    # `..` traversal must surface as a sentinel string from call_tool,
    # not a raised exception — the recovery contract is uniform.
    result = call_tool(
        "file_rewrite",
        tmp_path,
        path="../../../etc/passwd",
        operation="replace",
        content="malicious",
    )
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
    assert "escapes the sandbox" in result


def test_call_tool_dispatches_regex_extract(tiny_repo_root: Path):
    result = call_tool(
        "regex_extract",
        tiny_repo_root,
        pattern=r"Pangolin",
        path=".",
        max_matches=5,
    )
    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "pattern",
        "path",
        "matches",
        "match_count",
        "truncated",
    }
    assert result["pattern"] == "Pangolin"
    assert result["match_count"] >= 1
    # Each match is a dict (dataclass→dict via _serialize) with the
    # locked match-record keys.
    for match in result["matches"]:
        assert set(match.keys()) == {
            "path",
            "line_number",
            "match",
            "groups",
            "span",
        }


def test_call_tool_regex_extract_refuses_malformed_pattern(
    tiny_repo_root: Path,
):
    # Layer-1 refusal: re.compile must reject before any file IO.
    result = call_tool(
        "regex_extract",
        tiny_repo_root,
        pattern=r"[unclosed",
    )
    assert isinstance(result, str)
    assert result.startswith("ERROR:")
