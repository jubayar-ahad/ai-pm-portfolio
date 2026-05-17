"""Tests for evals_harness.report: scored.jsonl aggregation + CLI."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from evals_harness import _repo
from evals_harness.ingest import _write_normalized, ingest
from evals_harness.report import (
    MATCH_RUBRICS,
    NO_OBSERVATION,
    REQUIRED_CORE_KEYS,
    ReportError,
    _read_scored,
    _stats_cells,
    _summarize_cost,
    _summarize_match,
    cmd_report,
    render_report,
)
from evals_harness.score import (
    cmd_score,
)

_repo.ensure_build_imports_on_path()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def envelope_path(
    tmp_path: Path,
    queries_tiny_path: Path,
    traces_rag_path: Path,
    traces_tua_path: Path,
) -> Path:
    result = ingest(queries_tiny_path, [traces_rag_path, traces_tua_path])
    env = tmp_path / "ingested.jsonl"
    _write_normalized(env, result)
    return env


def _scored_files_for_all_rubrics(envelope_path: Path, tmp_path: Path) -> list[Path]:
    """Run score with each rubric and collect the resulting JSONL files."""
    paths: list[Path] = []
    for rubric in ("refusal", "groundedness", "first_call_tool", "termination", "cost"):
        out_path = tmp_path / f"scored_{rubric}.jsonl"
        args = argparse.Namespace(
            rubric=rubric,
            ingested=str(envelope_path),
            out=str(out_path),
            markdown=None,
        )
        # Capture stdout to keep test logs clean.
        with redirect_stdout(io.StringIO()):
            rc = cmd_score(args)
        assert rc == 0
        paths.append(out_path)
    return paths


def _capture(fn, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = fn(*args, **kwargs)
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_match_rubrics_lock():
    assert MATCH_RUBRICS == (
        "refusal",
        "groundedness",
        "first_call_tool",
        "termination",
    )


def test_required_core_keys():
    assert "rubric" in REQUIRED_CORE_KEYS
    assert "match" in REQUIRED_CORE_KEYS
    assert "record_id" in REQUIRED_CORE_KEYS


def test_no_observation_constant():
    assert NO_OBSERVATION == "no_observation"


# ---------------------------------------------------------------------------
# _read_scored
# ---------------------------------------------------------------------------


def test_read_scored_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    row = {
        "rubric": "refusal",
        "record_id": "r1",
        "schema_version": "rag-app.ask.v1",
        "question": "q",
        "label_id": "L1",
        "match": True,
    }
    p.write_text(json.dumps(row) + "\n\n\n", encoding="utf-8")
    rows = _read_scored([p])
    assert len(rows) == 1


def test_read_scored_rejects_bad_json(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ReportError, match="invalid JSON"):
        _read_scored([p])


def test_read_scored_rejects_non_object(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text('"a string is not allowed"\n', encoding="utf-8")
    with pytest.raises(ReportError, match="expected JSON object"):
        _read_scored([p])


def test_read_scored_rejects_missing_core_key(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text(
        json.dumps(
            {
                "rubric": "refusal",
                "record_id": "x",
                # missing schema_version
                "question": "q",
                "label_id": "L",
                "match": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReportError, match="missing required core key"):
        _read_scored([p])


def test_read_scored_rejects_unknown_rubric(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text(
        json.dumps(
            {
                "rubric": "imagined",
                "record_id": "x",
                "schema_version": "rag-app.ask.v1",
                "question": "q",
                "label_id": "L",
                "match": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReportError, match="unknown rubric"):
        _read_scored([p])


# ---------------------------------------------------------------------------
# _summarize_match / _summarize_cost
# ---------------------------------------------------------------------------


def test_summarize_match_observable_excludes_no_observation():
    rows = [
        {"match": True, "observed_outcome": "refuse"},
        {"match": False, "observed_outcome": "answer"},
        {"match": False, "observed_outcome": "no_observation"},
    ]
    s = _summarize_match(rows)
    assert s["n_total"] == 3
    assert s["n_observable"] == 2
    assert s["n_matched"] == 1
    assert "1/2" in s["accuracy"]


def test_summarize_match_empty_returns_na_accuracy():
    s = _summarize_match([])
    assert s["accuracy"] == "n/a"
    assert s["n_total"] == 0


def test_summarize_match_missing_observed_outcome_counts_as_unobserved():
    """Rows with no observed_outcome key (None) are not observable."""
    rows = [{"match": True}]
    s = _summarize_match(rows)
    assert s["n_observable"] == 0
    assert s["accuracy"] == "n/a"


def test_summarize_cost_returns_stats_when_observed():
    rows = [
        {
            "observed_outcome": "observed",
            "total_tokens": 100,
            "steps_taken": 1,
            "tool_latency_ms_sum": 50,
        },
        {
            "observed_outcome": "observed",
            "total_tokens": 200,
            "steps_taken": 2,
            "tool_latency_ms_sum": 80,
        },
        {"observed_outcome": "no_observation"},
    ]
    s = _summarize_cost(rows)
    assert s["n_total"] == 3
    assert s["n_observable"] == 2
    assert s["total_tokens"] is not None
    assert s["total_tokens"][0] == 2  # n
    assert s["steps_taken"] is not None
    assert s["tool_latency_ms_sum"] is not None


def test_summarize_cost_returns_none_when_no_observations():
    rows = [{"observed_outcome": "no_observation"}]
    s = _summarize_cost(rows)
    assert s["total_tokens"] is None
    assert s["steps_taken"] is None
    assert s["tool_latency_ms_sum"] is None


# ---------------------------------------------------------------------------
# _stats_cells
# ---------------------------------------------------------------------------


def test_stats_cells_renders_trio():
    assert _stats_cells((3, 10, 20, 30)) == "10 | 20 | 30"


def test_stats_cells_none_renders_na_trio():
    assert _stats_cells(None) == "n/a | n/a | n/a"


# ---------------------------------------------------------------------------
# render_report
# ---------------------------------------------------------------------------


def test_render_report_empty():
    md = render_report([], [Path("none.jsonl")])
    assert "# Eval report" in md
    assert "nothing to roll up" in md


def test_render_report_full_pipeline(envelope_path, tmp_path: Path):
    scored_paths = _scored_files_for_all_rubrics(envelope_path, tmp_path)
    rows = _read_scored(scored_paths)
    md = render_report(rows, scored_paths)
    assert "# Eval report" in md
    assert "## Quality rubrics" in md
    assert "## Cost rubric" in md
    assert "rag-app.ask.v1" in md
    assert "tool-use-agent.ask.v1" in md
    # TUA-only extras sub-table should appear because there are tua cost rows.
    assert "steps_taken p50" in md


def test_render_report_quality_only_no_cost(tmp_path: Path):
    """When the scored files contain only quality rubrics, the cost section
    must be omitted."""
    rows = [
        {
            "rubric": "refusal",
            "record_id": "r1",
            "schema_version": "rag-app.ask.v1",
            "question": "q",
            "label_id": "L1",
            "match": True,
            "observed_outcome": "answer",
        }
    ]
    md = render_report(rows, [Path("only_refusal.jsonl")])
    assert "## Quality rubrics" in md
    assert "## Cost rubric" not in md


def test_render_report_cost_only_no_quality(tmp_path: Path):
    rows = [
        {
            "rubric": "cost",
            "record_id": "r1",
            "schema_version": "rag-app.ask.v1",
            "question": "q",
            "label_id": "L1",
            "match": True,
            "observed_outcome": "observed",
            "total_tokens": 50,
            "steps_taken": None,
            "tool_latency_ms_sum": None,
        }
    ]
    md = render_report(rows, [Path("only_cost.jsonl")])
    assert "## Cost rubric" in md
    assert "## Quality rubrics" not in md


# ---------------------------------------------------------------------------
# cmd_report CLI dispatch
# ---------------------------------------------------------------------------


def test_cmd_report_empty_scored_list_returns_2(tmp_path: Path):
    args = argparse.Namespace(scored=[], markdown=None)
    rc, _, stderr = _capture(cmd_report, args)
    assert rc == 2
    assert "at least one --scored path is required" in stderr


def test_cmd_report_missing_file_returns_2(tmp_path: Path):
    args = argparse.Namespace(scored=[str(tmp_path / "nope.jsonl")], markdown=None)
    rc, _, stderr = _capture(cmd_report, args)
    assert rc == 2
    assert "scored file not found" in stderr


def test_cmd_report_bad_jsonl_returns_2(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text("{not json}\n", encoding="utf-8")
    args = argparse.Namespace(scored=[str(p)], markdown=None)
    rc, _, stderr = _capture(cmd_report, args)
    assert rc == 2
    assert "REPORT FAILED" in stderr


def test_cmd_report_writes_markdown(envelope_path, tmp_path: Path):
    scored_paths = _scored_files_for_all_rubrics(envelope_path, tmp_path)
    md_path = tmp_path / "out" / "report.md"
    args = argparse.Namespace(
        scored=[str(p) for p in scored_paths],
        markdown=str(md_path),
    )
    rc, stdout, _ = _capture(cmd_report, args)
    assert rc == 0
    assert md_path.is_file()
    assert "# Eval report" in stdout
    assert "# Eval report" in md_path.read_text(encoding="utf-8")


def test_cmd_report_prints_when_no_markdown(envelope_path, tmp_path: Path):
    scored_paths = _scored_files_for_all_rubrics(envelope_path, tmp_path)
    args = argparse.Namespace(
        scored=[str(p) for p in scored_paths],
        markdown=None,
    )
    rc, stdout, _ = _capture(cmd_report, args)
    assert rc == 0
    assert "Quality rubrics" in stdout
