"""Aggregate report rolling up per-rubric scored.jsonl files (slice 7).

Reads one or more ``scored.jsonl`` files produced by ``score`` (one per
rubric, or any subset) and renders a single Markdown report combining
every per-build × per-rubric summary. This is the artifact an
interviewer reads — one screenful, no per-record noise.

Two surfaces per input:

* **Quality rubrics** (``refusal`` / ``groundedness`` / ``first_call_tool``
  / ``termination``) — one row per (build, rubric) with the matched /
  observable accuracy. ``observed_outcome == "no_observation"`` rows are
  excluded from the denominator; this mirrors the slice 3–5a convention
  so the per-rubric and aggregate accuracies agree to the row.
* **Cost rubric** — one per-build row with ``total_tokens`` p50/p95/max,
  plus a tool-use-agent-only sub-table with ``steps_taken`` and
  ``tool_latency_ms_sum`` percentiles. Uses the locked ``_percentile``
  helper from ``score.py`` so the aggregate numbers byte-match the
  ``score --rubric cost`` report.

Out of scope (deferred to a follow-on iteration): ``corpus_fingerprint``
diversity warning. Adding it requires threading ``corpus_fingerprint``
through every per-rubric scored row schema first; doing it here would
silently break the slice 3–5b additive-schema lock.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .score import (
    ALL_RUBRICS,
    RUBRIC_COST,
    RUBRIC_FIRST_CALL_TOOL,
    RUBRIC_GROUNDEDNESS,
    RUBRIC_REFUSAL,
    RUBRIC_TERMINATION,
    SCHEMA_TOOL_USE_AGENT,
    _cost_stats,
)

# Quality rubrics share the cross-rubric core columns including a
# meaningful ``match`` boolean. The cost rubric's ``match`` is an
# observability flag (not a correctness signal) and is handled separately.
MATCH_RUBRICS: tuple[str, ...] = (
    RUBRIC_REFUSAL,
    RUBRIC_GROUNDEDNESS,
    RUBRIC_FIRST_CALL_TOOL,
    RUBRIC_TERMINATION,
)

NO_OBSERVATION = "no_observation"
COST_OBSERVED = "observed"

# Cross-rubric core columns every scored row must carry. Per-rubric
# extras (citations_total, stop_reason, total_tokens, ...) are allowed
# but not required by the aggregator.
REQUIRED_CORE_KEYS: tuple[str, ...] = (
    "rubric",
    "record_id",
    "schema_version",
    "question",
    "label_id",
    "match",
)


class ReportError(RuntimeError):
    """Raised on malformed scored input or unknown rubric."""


def _read_scored(paths: list[Path]) -> list[dict[str, Any]]:
    """Read every line of every scored.jsonl into a list of dicts.

    Validates the cross-rubric core columns and the rubric enum on each
    line; an unknown rubric or missing core column raises ``ReportError``
    with ``file:lineno`` context.
    """
    rows: list[dict[str, Any]] = []
    for path in paths:
        with open(path, encoding="utf-8") as fp:
            for lineno, raw in enumerate(fp, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ReportError(
                        f"{path}:{lineno}: invalid JSON ({exc.msg})"
                    ) from exc
                if not isinstance(rec, dict):
                    raise ReportError(
                        f"{path}:{lineno}: expected JSON object, "
                        f"got {type(rec).__name__}"
                    )
                missing = [k for k in REQUIRED_CORE_KEYS if k not in rec]
                if missing:
                    raise ReportError(
                        f"{path}:{lineno}: missing required core key(s) "
                        f"{missing}"
                    )
                if rec["rubric"] not in ALL_RUBRICS:
                    raise ReportError(
                        f"{path}:{lineno}: unknown rubric "
                        f"{rec['rubric']!r}; expected one of "
                        f"{sorted(ALL_RUBRICS)}"
                    )
                rows.append(rec)
    return rows


def _summarize_match(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate one (build, match-rubric) bucket.

    ``observable`` excludes ``no_observation`` rows (mirrors slices 3–5a).
    ``accuracy`` is ``matched / observable`` as ``X/Y (P.P%)``, or
    ``n/a`` when nothing was observable.
    """
    n_total = len(rows)
    n_observable = sum(
        1
        for r in rows
        if r.get("observed_outcome") not in (None, NO_OBSERVATION)
    )
    n_matched = sum(1 for r in rows if bool(r.get("match")))
    if n_observable:
        pct = 100.0 * n_matched / n_observable
        accuracy = f"{n_matched}/{n_observable} ({pct:.1f}%)"
    else:
        accuracy = "n/a"
    return {
        "n_total": n_total,
        "n_observable": n_observable,
        "n_matched": n_matched,
        "accuracy": accuracy,
    }


def _summarize_cost(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate one (build, cost) bucket.

    Returns total_tokens stats for all builds and steps_taken /
    tool_latency_ms_sum stats keyed under their names (None on builds
    where those fields are always null, e.g. rag-app rows). Uses the
    locked ``_cost_stats`` helper from ``score.py`` so the percentiles
    byte-match ``score --rubric cost`` output.
    """
    observed = [
        r for r in rows if r.get("observed_outcome") == COST_OBSERVED
    ]
    totals = [
        r["total_tokens"]
        for r in observed
        if isinstance(r.get("total_tokens"), int)
    ]
    steps_vals = [
        r["steps_taken"]
        for r in observed
        if isinstance(r.get("steps_taken"), int)
    ]
    lat_vals = [
        r["tool_latency_ms_sum"]
        for r in observed
        if isinstance(r.get("tool_latency_ms_sum"), int)
    ]
    n, p50, p95, mx = _cost_stats(totals)
    s_n, s_p50, s_p95, s_max = _cost_stats(steps_vals)
    l_n, l_p50, l_p95, l_max = _cost_stats(lat_vals)
    return {
        "n_total": len(rows),
        "n_observable": len(observed),
        "total_tokens": (n, p50, p95, mx) if n else None,
        "steps_taken": (s_n, s_p50, s_p95, s_max) if s_n else None,
        "tool_latency_ms_sum": (
            (l_n, l_p50, l_p95, l_max) if l_n else None
        ),
    }


def _stats_cells(stats: tuple[int, int, int, int] | None) -> str:
    """Render a ``p50 | p95 | max`` cell trio, or three n/a placeholders."""
    if stats is None:
        return "n/a | n/a | n/a"
    _, p50, p95, mx = stats
    return f"{p50} | {p95} | {mx}"


def render_report(
    rows: list[dict[str, Any]], scored_paths: list[Path]
) -> str:
    """Render the single combined Markdown report.

    Section order is fixed: header counts → quality rubrics table →
    cost rubric table → cost rubric tua-only extras. Each section is
    omitted when its underlying bucket is empty so the rendered
    document stays minimal.
    """
    schemas_seen = sorted({r["schema_version"] for r in rows})
    rubrics_seen = sorted({r["rubric"] for r in rows})

    lines: list[str] = []
    lines.append("# Eval report")
    lines.append("")
    lines.append(
        f"scored_files={len(scored_paths)}  total_rows={len(rows)}  "
        f"builds={','.join(schemas_seen) or '(none)'}  "
        f"rubrics={','.join(rubrics_seen) or '(none)'}"
    )
    lines.append("")
    if not rows:
        lines.append("(no scored rows — nothing to roll up)")
        return "\n".join(lines) + "\n"

    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        by_pair.setdefault((r["schema_version"], r["rubric"]), []).append(r)

    # ----- Quality rubrics table (match / observable accuracy) -----
    quality_pairs = [
        (schema, rub)
        for schema in schemas_seen
        for rub in MATCH_RUBRICS
        if (schema, rub) in by_pair
    ]
    if quality_pairs:
        lines.append(
            "## Quality rubrics (per-build × per-rubric accuracy)"
        )
        lines.append("")
        lines.append(
            "| build | rubric | n_rows | observable | accuracy |"
        )
        lines.append("| --- | --- | --- | --- | --- |")
        for schema, rub in quality_pairs:
            summary = _summarize_match(by_pair[(schema, rub)])
            lines.append(
                f"| {schema} | {rub} | {summary['n_total']} "
                f"| {summary['n_observable']} | {summary['accuracy']} |"
            )
        lines.append("")

    # ----- Cost rubric per-build totals + tua-only sub-table -----
    cost_pairs = [
        (schema, by_pair[(schema, RUBRIC_COST)])
        for schema in schemas_seen
        if (schema, RUBRIC_COST) in by_pair
    ]
    if cost_pairs:
        lines.append("## Cost rubric (per-build aggregate stats)")
        lines.append("")
        lines.append(
            "| build | n_rows | observable | total_tokens p50 "
            "| total_tokens p95 | total_tokens max |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- |")
        cost_summaries: dict[str, dict[str, Any]] = {}
        for schema, c_rows in cost_pairs:
            summary = _summarize_cost(c_rows)
            cost_summaries[schema] = summary
            lines.append(
                f"| {schema} | {summary['n_total']} "
                f"| {summary['n_observable']} "
                f"| {_stats_cells(summary['total_tokens'])} |"
            )
        # Tool-use-agent-only second table: steps_taken + tool_latency_ms_sum.
        tua = cost_summaries.get(SCHEMA_TOOL_USE_AGENT)
        if tua is not None and (
            tua["steps_taken"] is not None
            or tua["tool_latency_ms_sum"] is not None
        ):
            lines.append("")
            lines.append(
                "| build | steps_taken p50 | steps_taken p95 "
                "| steps_taken max | tool_latency_ms_sum p50 "
                "| tool_latency_ms_sum p95 | tool_latency_ms_sum max |"
            )
            lines.append(
                "| --- | --- | --- | --- | --- | --- | --- |"
            )
            lines.append(
                f"| {SCHEMA_TOOL_USE_AGENT} "
                f"| {_stats_cells(tua['steps_taken'])} "
                f"| {_stats_cells(tua['tool_latency_ms_sum'])} |"
            )
    return "\n".join(lines) + "\n"


def cmd_report(args: argparse.Namespace) -> int:
    """CLI entry point for ``python -m evals_harness report``."""
    paths = [Path(p) for p in args.scored]
    if not paths:
        print(
            "REPORT FAILED: at least one --scored path is required",
            file=sys.stderr,
        )
        return 2
    for p in paths:
        if not p.is_file():
            print(
                f"REPORT FAILED: scored file not found: {p}",
                file=sys.stderr,
            )
            return 2
    try:
        rows = _read_scored(paths)
    except ReportError as exc:
        print(f"REPORT FAILED: {exc}", file=sys.stderr)
        return 2

    report = render_report(rows, paths)

    if args.markdown:
        out_path = Path(args.markdown)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")

    print(report, end="")
    return 0
