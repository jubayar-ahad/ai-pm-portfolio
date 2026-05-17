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

EXPECTED_TOOL_NAMES: tuple[str, ...] = (
    "list_repo_files",
    "read_repo_file",
    "grep_repo",
    "list_pipeline_rows",
    "count_by_stage",
    "count_by_bucket",
    "sql_query",
    "file_rewrite",
)


def test_catalog_has_eight_tools_in_locked_order():
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
