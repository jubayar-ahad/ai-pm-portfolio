"""Command-line entry point for the tool-use-agent demo.

As of this iteration: `catalog` (print JSON schemas), `tool` (invoke any
registered tool directly, no API key needed), and `ask` (bounded
multi-step agent loop with `--max-steps` knob; auto-falls back to a
key-free dry-run that prints the assembled prompt and the tool catalog).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import Any

from tool_use_agent.agent import (
    DEFAULT_MAX_STEPS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    AgentResult,
    build_dry_run_result,
    run_agent,
)
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


def _agent_result_to_payload(result: AgentResult) -> dict[str, Any]:
    """Render an AgentResult as a JSON-friendly dict for `ask --json`.

    Slice 5 will add the trace-record fields (schema_version, record_id,
    corpus_fingerprint, generated_at) to this payload by reusing the
    rag-app trace helpers — the shape here is the slice-3 baseline.
    """
    return {
        "mode": result.mode,
        "question": result.question,
        "prompt": {
            "system": result.system_prompt,
            "user": result.user_message,
        },
        "max_steps": result.max_steps,
        "steps_taken": result.steps_taken,
        "tool_calls": [dataclasses.asdict(call) for call in result.tool_calls],
        "stop_reason": result.stop_reason,
        "refusal_reason": result.refusal_reason,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "final_text": result.final_text,
    }


def _print_agent_result_human(result: AgentResult) -> None:
    print(f"Question: {result.question}")
    print(f"Mode: {result.mode}")
    if result.mode == "dry-run":
        print(f"Max steps: {result.max_steps}")
        print("--- prompt.system ---")
        print(result.system_prompt)
        print("--- prompt.user ---")
        print(result.user_message)
        print()
        print(f"--- catalog ({len(CATALOG)} tools the model would see) ---")
        for tool in CATALOG.values():
            print(f"  - {tool.name}: {tool.description}")
        print()
        print("(dry-run: no model call made)")
        return

    if result.tool_calls:
        print(
            f"--- tool trace ({len(result.tool_calls)} call(s) over "
            f"{result.steps_taken}/{result.max_steps} step(s)) ---"
        )
        for call in result.tool_calls:
            tag = " [ERROR]" if call.is_error else ""
            print(f"  step {call.step}: {call.tool}({call.input}){tag}")
            preview = _preview_output(call.output)
            print(f"    -> {preview}")
    else:
        print(f"(no tool calls; steps_taken={result.steps_taken})")
    print()
    print("--- answer ---")
    print(result.final_text or "(empty)")
    print()
    refusal = (
        f"  refusal_reason={result.refusal_reason}"
        if result.refusal_reason
        else ""
    )
    print(
        f"(model={result.model}  stop_reason={result.stop_reason}{refusal}  "
        f"steps={result.steps_taken}/{result.max_steps}  "
        f"input_tokens={result.input_tokens}  "
        f"output_tokens={result.output_tokens})"
    )


def _preview_output(output: Any, limit: int = 200) -> str:
    """One-line summary of a tool output for the human trace view."""
    if isinstance(output, str):
        text = output.replace("\n", " ")
    else:
        try:
            text = json.dumps(output, ensure_ascii=False, default=str)
        except TypeError:
            text = repr(output)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def cmd_ask(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path(__file__).resolve().parent)
    have_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if args.max_steps < 1:
        print(
            f"error: --max-steps must be >= 1 (got {args.max_steps})",
            file=sys.stderr,
        )
        return 2

    if args.dry_run or not have_key:
        result = build_dry_run_result(args.question, max_steps=args.max_steps)
    else:
        result = run_agent(
            args.question,
            repo_root=repo_root,
            model=args.model,
            max_tokens=args.max_tokens,
            max_steps=args.max_steps,
        )

    if args.json:
        payload = _agent_result_to_payload(result)
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return 0

    if args.dry_run is False and not have_key:
        # Surface the auto-fallback so the user understands why no model
        # call happened — same pattern as the rag-app `ask` subcommand.
        print("(no ANTHROPIC_API_KEY in environment — falling back to dry-run)")
    _print_agent_result_human(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tool_use_agent",
        description=(
            "Tool-use agent demo: catalog + direct tool calls + "
            "bounded multi-step ask."
        ),
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

    ask = subparsers.add_parser(
        "ask",
        help=(
            "Run the bounded multi-step agent loop on a question. "
            "Auto-falls back to a key-free dry-run if ANTHROPIC_API_KEY "
            "is unset."
        ),
    )
    ask.add_argument("question", help="Natural-language question.")
    ask.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Anthropic model id (default {DEFAULT_MODEL}).",
    )
    ask.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Max output tokens per turn (default {DEFAULT_MAX_TOKENS}).",
    )
    ask.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        help=(
            f"Max tool-execution rounds before the loop exits with "
            f"stop_reason=max_steps_exhausted and the canonical "
            f"refusal sentence as final_text (default "
            f"{DEFAULT_MAX_STEPS})."
        ),
    )
    ask.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Build and print the prompt + catalog without calling Claude. "
            "Auto-enabled if ANTHROPIC_API_KEY is unset."
        ),
    )
    ask.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit a structured JSON record (prompt, tool_calls, answer) "
            "for downstream tooling. Trace-record fields land in slice 5."
        ),
    )
    ask.set_defaults(func=cmd_ask)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
