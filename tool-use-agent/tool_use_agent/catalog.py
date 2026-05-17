"""Tool registry and JSON schemas for the tool-use-agent.

Each registered tool has:
- a stable `name` the LLM (and `python -m tool_use_agent tool <name>`) refer to
- a one-line `description` that ships in the prompt the model sees
- a JSON Schema (`input_schema`) for parameter validation
- a Python callable that takes `(repo_root, **kwargs)` and returns a value

The catalog is built once and frozen. Adding a tool means appending to
`build_catalog()` here — the dispatcher (`call_tool`) and the CLI both
discover tools through the catalog with no per-tool wiring elsewhere.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable

from tool_use_agent.tools_pipeline import (
    ACTIVE_STAGES,
    ALL_STAGES,
    BUCKETS,
    TERMINAL_STAGES,
    count_by_bucket,
    count_by_stage,
    list_pipeline_rows,
)
from tool_use_agent.tools_repo import (
    grep_repo,
    list_repo_files,
    read_repo_file,
)
from tool_use_agent.tools_regex import regex_extract
from tool_use_agent.tools_rewrite import OPERATIONS as REWRITE_OPERATIONS
from tool_use_agent.tools_rewrite import file_rewrite
from tool_use_agent.tools_sql import sql_query


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    impl: Callable[..., Any]


def _serialize(value: Any) -> Any:
    """JSON-friendly normalization for tool return values.

    Dataclasses become dicts; lists/tuples/dicts recurse. Everything else is
    returned as-is and falls to the JSON encoder's defaults at the CLI
    boundary.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _serialize(v) for k, v in asdict(value).items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def build_catalog() -> dict[str, Tool]:
    """Construct the catalog. Order is deliberate and observable."""
    tools: list[Tool] = [
        Tool(
            name="list_repo_files",
            description=(
                "Enumerate repo-relative file paths matching a glob pattern "
                "under a directory. Recursive by default. Read-only."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": (
                            "Repo-relative directory to enumerate under. "
                            "Defaults to the repo root."
                        ),
                        "default": ".",
                    },
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Glob pattern. `**` is honored. Default '*.md' "
                            "matches markdown files recursively."
                        ),
                        "default": "*.md",
                    },
                },
                "additionalProperties": False,
            },
            impl=list_repo_files,
        ),
        Tool(
            name="read_repo_file",
            description=(
                "Read a 1-indexed inclusive line range from a repo file. "
                "Returns an 'ERROR: ...' string on bad input (not an "
                "exception)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Repo-relative path to the file.",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "First line to include (1-indexed).",
                        "minimum": 1,
                        "default": 1,
                    },
                    "end_line": {
                        "type": ["integer", "null"],
                        "description": (
                            "Last line to include (inclusive). Null means "
                            "read through end-of-file."
                        ),
                        "default": None,
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            impl=read_repo_file,
        ),
        Tool(
            name="grep_repo",
            description=(
                "Case-insensitive substring search across text files under "
                "a path. Returns up to `max_matches` records of "
                "{path, line_number, line}. Read-only."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Substring to search for.",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Repo-relative file or directory to search "
                            "under. Defaults to the repo root."
                        ),
                        "default": ".",
                    },
                    "max_matches": {
                        "type": "integer",
                        "description": "Cap on returned matches.",
                        "minimum": 1,
                        "default": 20,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            impl=grep_repo,
        ),
        Tool(
            name="list_pipeline_rows",
            description=(
                "Parse the interview-pipeline tracker and return active "
                "rows, optionally filtered by `stage` and/or `bucket`. "
                "Placeholder rows are excluded."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "stage": {
                        "type": ["string", "null"],
                        "description": (
                            "Stage filter. One of the locked stage strings "
                            "or null for no filter."
                        ),
                        "enum": list(ALL_STAGES) + [None],
                        "default": None,
                    },
                    "bucket": {
                        "type": ["string", "null"],
                        "description": (
                            "Bucket filter. One of B1/B2/B3 or null for "
                            "no filter."
                        ),
                        "enum": list(BUCKETS) + [None],
                        "default": None,
                    },
                },
                "additionalProperties": False,
            },
            impl=list_pipeline_rows,
        ),
        Tool(
            name="count_by_stage",
            description=(
                "Histogram of active-pipeline rows by stage. Returns a "
                "dict keyed by every locked stage string (zeros included)."
            ),
            input_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            impl=count_by_stage,
        ),
        Tool(
            name="count_by_bucket",
            description=(
                "Histogram of active-pipeline rows by bucket (B1/B2/B3). "
                "Surfaces Bucket-2 share at a glance."
            ),
            input_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            impl=count_by_bucket,
        ),
        Tool(
            name="sql_query",
            description=(
                "Execute a read-only SQL SELECT against a repo-relative "
                "SQLite database file and return rows as JSON. Write "
                "keywords (INSERT/UPDATE/DELETE/DDL) are rejected before "
                "the database is opened; the connection itself is opened "
                "in URI read-only mode (`mode=ro`) as a redundant layer."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Repo-relative path to a SQLite database file."
                        ),
                    },
                    "sql": {
                        "type": "string",
                        "description": (
                            "Single SELECT statement to execute. Multiple "
                            "statements separated by `;` are rejected."
                        ),
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": (
                            "Cap on returned rows (1–1000). Defaults to 100."
                        ),
                        "minimum": 1,
                        "default": 100,
                    },
                },
                "required": ["path", "sql"],
                "additionalProperties": False,
            },
            impl=sql_query,
        ),
        Tool(
            name="file_rewrite",
            description=(
                "Apply a structured edit (replace/append/prepend) to a "
                "file under tool-use-agent/sandbox/ and return the unified "
                "diff. Paths are sandbox-relative; anything resolving "
                "outside the sandbox is refused. The target file must "
                "already exist."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Sandbox-relative path (e.g. 'notes.md'). "
                            "Refused if it escapes the sandbox root."
                        ),
                    },
                    "operation": {
                        "type": "string",
                        "description": (
                            "Edit operation: replace (full overwrite), "
                            "append (suffix), or prepend (prefix)."
                        ),
                        "enum": sorted(REWRITE_OPERATIONS),
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "Text to write (full content for replace; "
                            "suffix for append; prefix for prepend)."
                        ),
                    },
                },
                "required": ["path", "operation", "content"],
                "additionalProperties": False,
            },
            impl=file_rewrite,
        ),
        Tool(
            name="regex_extract",
            description=(
                "Walk text files under a repo-relative path and return "
                "regex matches with line numbers and capture groups. "
                "Useful for the agent's own 'find places to change' "
                "reasoning. Read-only. The pattern is a Python re-style "
                "regex; use `(?i)` inline for case insensitivity."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Python re-style regex pattern. Compiled "
                            "before any file IO; malformed patterns are "
                            "refused with an ERROR string."
                        ),
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Repo-relative file or directory to scan. "
                            "Defaults to the repo root."
                        ),
                        "default": ".",
                    },
                    "max_matches": {
                        "type": "integer",
                        "description": (
                            "Cap on returned matches (1–1000). "
                            "Defaults to 20."
                        ),
                        "minimum": 1,
                        "default": 20,
                    },
                },
                "required": ["pattern"],
                "additionalProperties": False,
            },
            impl=regex_extract,
        ),
    ]
    return {tool.name: tool for tool in tools}


CATALOG: dict[str, Tool] = build_catalog()


def call_tool(name: str, repo_root: Path, **kwargs: Any) -> Any:
    """Dispatch a tool call by name. Raises KeyError if the name is unknown.

    The dispatcher does not enforce the JSON schema beyond what Python's own
    argument-binding does — the live agent loop (slice 2) relies on the
    Anthropic SDK's tool-use API to validate inputs against the schema
    before calling here. The CLI uses argparse types to do the same job
    for direct invocation.
    """
    if name not in CATALOG:
        raise KeyError(f"unknown tool: {name!r}")
    result = CATALOG[name].impl(repo_root, **kwargs)
    return _serialize(result)


def catalog_as_anthropic_tools() -> list[dict[str, Any]]:
    """Render the catalog in the Anthropic SDK's tools=[…] schema.

    Returned shape matches the `{name, description, input_schema}` contract
    the Messages API expects. Slice 2 will hand this directly to
    `client.messages.create(tools=...)`.
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }
        for tool in CATALOG.values()
    ]


# Re-export stage/bucket vocab for callers that want them without reaching
# into tools_pipeline directly.
__all__ = [
    "ACTIVE_STAGES",
    "ALL_STAGES",
    "BUCKETS",
    "CATALOG",
    "TERMINAL_STAGES",
    "Tool",
    "build_catalog",
    "call_tool",
    "catalog_as_anthropic_tools",
]
