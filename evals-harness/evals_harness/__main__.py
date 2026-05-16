"""``python -m evals_harness`` CLI entry point.

Three subcommands will land across slices 2–5. Slice 2 ships ``ingest``;
``score`` and ``report`` will be added by future iterations without
changing the CLI shape.
"""

from __future__ import annotations

import argparse
import sys

from .ingest import cmd_ingest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evals_harness",
        description=(
            "Cross-build evaluations harness for rag-app and "
            "tool-use-agent. See evals-harness/README.md."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser(
        "ingest",
        help="Validate labels + traces and run startup invariants.",
    )
    p_ingest.add_argument(
        "--labels",
        required=True,
        help="Path to a JSONL labeled-query file (queries.jsonl).",
    )
    p_ingest.add_argument(
        "--traces",
        nargs="*",
        default=[],
        help=(
            "Zero or more JSONL trace files. Each line must be an "
            "ask --json record from rag-app or tool-use-agent."
        ),
    )
    p_ingest.add_argument(
        "--out",
        default=None,
        help=(
            "Optional path for the normalized ingested.jsonl. "
            "Omit to validate without writing."
        ),
    )
    p_ingest.add_argument(
        "--verbose",
        action="store_true",
        help="Print one line per passed invariant check.",
    )
    p_ingest.set_defaults(func=cmd_ingest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
