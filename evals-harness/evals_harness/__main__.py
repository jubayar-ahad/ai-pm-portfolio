"""``python -m evals_harness`` CLI entry point.

Three subcommands land across slices 2–5. Slices 2 and 3 ship ``ingest``
and ``score``; ``report`` (slice 5) will be added without changing the
CLI shape.
"""

from __future__ import annotations

import argparse
import sys

from .ingest import cmd_ingest
from .score import ALL_RUBRICS, cmd_score


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

    p_score = sub.add_parser(
        "score",
        help=(
            "Score a normalized ingested.jsonl against a labeled set. "
            "Slice 3 wires 'refusal'; slice 4 adds 'groundedness' "
            "(rag-app only) and 'first_call_tool' (tool-use-agent only); "
            "slice 5a adds 'termination' (tool-use-agent only); "
            "slice 5b adds 'cost' (cross-build, aggregate stats)."
        ),
    )
    p_score.add_argument(
        "--rubric",
        required=True,
        choices=list(ALL_RUBRICS),
        help=(
            "Which rubric to score. 'refusal' is cross-build; "
            "'groundedness' applies only to rag-app traces; "
            "'first_call_tool' and 'termination' apply only to "
            "tool-use-agent traces; 'cost' is cross-build (aggregate "
            "p50/p95/max stats over live traces)."
        ),
    )
    p_score.add_argument(
        "--ingested",
        required=True,
        help=(
            "Path to a normalized ingested.jsonl produced by "
            "`python -m evals_harness ingest --out`."
        ),
    )
    p_score.add_argument(
        "--out",
        default=None,
        help=(
            "Optional path for per-record scored JSONL. Each line is one "
            "(record_id, rubric) row with expected/observed outcomes."
        ),
    )
    p_score.add_argument(
        "--markdown",
        default=None,
        help=(
            "Optional path to write the rendered Markdown report. The "
            "report always prints to stdout regardless."
        ),
    )
    p_score.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
