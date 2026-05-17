"""Tests for tool_use_agent.tools_pipeline: parse + filter + histograms."""

from __future__ import annotations

from pathlib import Path

import pytest

from tool_use_agent.tools_pipeline import (
    ACTIVE_STAGES,
    ALL_STAGES,
    BUCKETS,
    TERMINAL_STAGES,
    PipelineRow,
    count_by_bucket,
    count_by_stage,
    list_pipeline_rows,
)


def test_stage_vocab_partition():
    # ALL_STAGES is the concat; the two halves are disjoint.
    assert ALL_STAGES == ACTIVE_STAGES + TERMINAL_STAGES
    assert set(ACTIVE_STAGES).isdisjoint(set(TERMINAL_STAGES))


def test_buckets_locked():
    assert BUCKETS == ("B1", "B2", "B3")


def test_list_pipeline_rows_parses_fixture(tiny_repo_root: Path):
    rows = list_pipeline_rows(tiny_repo_root)
    assert len(rows) == 4  # Four real rows (one placeholder excluded).
    companies = [r.company for r in rows]
    assert companies == ["Acme", "Beta Corp", "Gamma", "Delta"]


def test_list_pipeline_rows_excludes_placeholder(tiny_repo_root: Path):
    rows = list_pipeline_rows(tiny_repo_root)
    for r in rows:
        assert not r.company.startswith("_<")


def test_list_pipeline_rows_returns_pipelinerow_instances(tiny_repo_root: Path):
    rows = list_pipeline_rows(tiny_repo_root)
    assert all(isinstance(r, PipelineRow) for r in rows)


def test_list_pipeline_rows_stage_filter(tiny_repo_root: Path):
    rows = list_pipeline_rows(tiny_repo_root, stage="panel")
    assert len(rows) == 1
    assert rows[0].company == "Beta Corp"


def test_list_pipeline_rows_bucket_filter(tiny_repo_root: Path):
    rows = list_pipeline_rows(tiny_repo_root, bucket="B2")
    assert len(rows) == 2
    assert {r.company for r in rows} == {"Beta Corp", "Gamma"}


def test_list_pipeline_rows_combined_filter(tiny_repo_root: Path):
    rows = list_pipeline_rows(tiny_repo_root, stage="hiring-manager", bucket="B2")
    assert len(rows) == 1
    assert rows[0].company == "Gamma"


def test_list_pipeline_rows_unknown_stage_returns_empty(tiny_repo_root: Path):
    assert list_pipeline_rows(tiny_repo_root, stage="not-a-stage") == []


def test_list_pipeline_rows_unknown_bucket_returns_empty(tiny_repo_root: Path):
    assert list_pipeline_rows(tiny_repo_root, bucket="B9") == []


def test_list_pipeline_rows_missing_tracker_returns_empty(tmp_path: Path):
    # tmp_path has no templates/INTERVIEW_TRACKER.md → return empty.
    assert list_pipeline_rows(tmp_path) == []


def test_count_by_stage_keys_cover_all_stages(tiny_repo_root: Path):
    counts = count_by_stage(tiny_repo_root)
    # Every locked stage appears as a key, even with zero rows.
    for stage in ALL_STAGES:
        assert stage in counts
    assert counts["applied"] == 1
    assert counts["panel"] == 1
    assert counts["hiring-manager"] == 1
    assert counts["recruiter-screen"] == 1
    # Stages with no rows are 0, not missing.
    assert counts["sourced"] == 0
    assert counts["offer-verbal"] == 0


def test_count_by_stage_totals_match_row_count(tiny_repo_root: Path):
    counts = count_by_stage(tiny_repo_root)
    rows = list_pipeline_rows(tiny_repo_root)
    assert sum(counts.values()) == len(rows)


def test_count_by_bucket_returns_b1_b2_b3(tiny_repo_root: Path):
    counts = count_by_bucket(tiny_repo_root)
    assert set(counts.keys()) >= set(BUCKETS)
    assert counts["B1"] == 1
    assert counts["B2"] == 2
    assert counts["B3"] == 1


def test_count_by_bucket_zero_rows_when_tracker_missing(tmp_path: Path):
    counts = count_by_bucket(tmp_path)
    assert counts == {"B1": 0, "B2": 0, "B3": 0}


def test_malformed_table_returns_no_rows(tmp_path: Path):
    # Tracker exists but the table is missing its `|---|` separator row.
    tracker = tmp_path / "templates" / "INTERVIEW_TRACKER.md"
    tracker.parent.mkdir(parents=True)
    tracker.write_text(
        "# Stub\n\n## Active pipeline\n\n"
        "| # | Company | Role title | Bucket | Source | Stage | Next action | Due | Comp | JD | Contact | Notes |\n"
        "| 1 | Acme | AI PM | B1 | direct apply | applied | follow up | 2026-06-01 | $200k | https://x | Pat | n/a |\n",
        encoding="utf-8",
    )
    assert list_pipeline_rows(tmp_path) == []


def test_missing_active_heading_returns_no_rows(tmp_path: Path):
    tracker = tmp_path / "templates" / "INTERVIEW_TRACKER.md"
    tracker.parent.mkdir(parents=True)
    tracker.write_text("# Tracker without the active section heading\n", encoding="utf-8")
    assert list_pipeline_rows(tmp_path) == []
