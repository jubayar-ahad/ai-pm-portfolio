"""Command-line entry point for the tool-use-agent demo.

As of this iteration: `catalog` (print JSON schemas) and `tool` (invoke any
registered tool directly, no API key needed). Subsequent slices will add
`ask` (single-step loop, then multi-step) per the README roadmap.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tool_use_agent.catalog import (
    CATALOG,
    Tool,
    call_tool,
    catalog_as_anthropic_tools,
)
from tool_use_agent.tools_repo import find_repo_root


def _json_default(obj: Any) -> Any:
    # Anything still unrecognized after catalog._serialize falls here.
    raise TypeError(f"object of type {type(obj).__name__} is not JSON-serializable")


def _add_tool_argparse_flags(
    sub: argparse.ArgumentParser, tool: Tool
) -> None:
    """Materialize a tool's JSON schema as argparse flags.

    Supports the four JSON-schema property types this catalog uses:
    string, integer, ["string", "null"], ["integer", "null"]. Enum values
    constrain `choices`. Defaults from the schema become argparse defaults.
    """
    properties = tool.input_schema.get("properties", {})
    required = set(tool.input_schema.get("required", ()))
    for prop_name, prop in properties.items():
        prop_type = prop.get("type")
        flag = f"--{prop_name.replace('_', '-')}"
        kwargs: dict[str, Any] = {
            "dest": prop_name,
            "help": prop.get("description", ""),
        }
        is_optional = (
            isinstance(prop_type, list) and "null" in prop_type
        )
        # Coerce composite type to its scalar member for argparse `type=`.
        scalar_type = prop_type
        if isinstance(prop_type, list):
            scalar_type = next(
                (t for t in prop_type if t != "null"), "string"
            )
        if scalar_type == "integer":
            kwargs["type"] = int
        else:
            kwargs["type"] = str
        if "enum" in prop:
            choices = [c for c in prop["enum"] if c is not None]
            kwargs["choices"] = choices
        if prop_name in required and not is_optional:
            kwargs["required"] = True
        else:
            kwargs["default"] = prop.get("default", None)
        sub.add_argument(flag, **kwargs)


def cmd_catalog(args: argparse.Namespace) -> int:
    payload = catalog_as_anthropic_tools()
    json.dump(payload, sys.stdout, indent=2, default=_json_default)
    sys.stdout.write("\n")
    return 0


def cmd_tool(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path(__file__).resolve().parent)
    tool = CATALOG[args.tool_name]
    # Pull the property names off the schema so we only forward known kwargs.
    schema_props = tool.input_schema.get("properties", {})
    kwargs = {
        name: getattr(args, name)
        for name in schema_props
        if getattr(args, name, None) is not None
    }
    result = call_tool(args.tool_name, repo_root, **kwargs)
    if args.json:
        json.dump(result, sys.stdout, indent=2, default=_json_default)
        sys.stdout.write("\n")
    else:
        _print_human(args.tool_name, result)
    return 0


def _print_human(tool_name: str, result: Any) -> None:
    """Pretty-print a tool result without dumping raw Python repr.

    Lists of dicts (e.g. grep_repo matches, pipeline rows) become aligned
    rows; scalar dicts (count_by_*) become `key: value` lines; strings
    (read_repo_file) print as-is; lists of strings (list_repo_files)
    print one per line. Falls back to JSON for anything else.
    """
    if isinstance(result, str):
        print(result)
        return
    if isinstance(result, list):
        if not result:
            print(f"(no results from {tool_name})")
            return
        if all(isinstance(item, str) for item in result):
            for item in result:
                print(item)
            return
        if all(isinstance(item, dict) for item in result):
            for item in result:
                pieces = [f"{k}={v!r}" for k, v in item.items()]
                print(" | ".join(pieces))
            return
    if isinstance(result, dict):
        width = max((len(k) for k in result), default=0)
        for key, value in result.items():
            print(f"{key.ljust(width)}  {value}")
        return
    json.dump(result, sys.stdout, indent=2, default=_json_default)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tool_use_agent",
        description="Tool-use agent demo (slice 1: catalog + direct tool calls).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    cat = subparsers.add_parser(
        "catalog",
        help="Print the tool catalog as Anthropic-tools-compatible JSON.",
    )
    cat.set_defaults(func=cmd_catalog)

    tool_parser = subparsers.add_parser(
        "tool",
        help="Invoke a registered tool directly. No API key required.",
    )
    tool_subs = tool_parser.add_subparsers(dest="tool_name", required=True)
    for tool in CATALOG.values():
        sub = tool_subs.add_parser(tool.name, help=tool.description)
        _add_tool_argparse_flags(sub, tool)
        sub.add_argument(
            "--json",
            action="store_true",
            help="Emit the tool result as JSON instead of a human-readable view.",
        )
        sub.set_defaults(func=cmd_tool)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
