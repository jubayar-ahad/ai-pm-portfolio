"""Tests for evals_harness.score: classifiers + 5 rubrics + renderers + CLI."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from evals_harness import _repo
from evals_harness.ingest import _write_normalized, ingest
from evals_harness.score import (
    ALL_RUBRICS,
    COST_NONE,
    COST_OBSERVED,
    FIRST_CALL_MATCH,
    FIRST_CALL_MISMATCH,
    FIRST_CALL_NONE,
    GROUNDED_FALSE,
    GROUNDED_NONE,
    GROUNDED_TRUE,
    OBSERVED_ANSWER,
    OBSERVED_NONE,
    OBSERVED_REFUSE,
    RUBRIC,
    RUBRIC_REFUSAL,
    SCHEMA_RAG_APP,
    SCHEMA_TOOL_USE_AGENT,
    ScoreError,
    TERMINATION_CLEAN,
    TERMINATION_MAX_STEPS,
    TERMINATION_MODEL_REFUSED,
    TERMINATION_NONE,
    TERMINATION_REPEATED_ERROR,
    _cost_stats,
    _extract_cost_rag_app,
    _extract_cost_tool_use_agent,
    _extract_first_tool,
    _extract_groundedness,
    _extract_termination,
    _percentile,
    _read_envelope,
    classify,
    classify_rag_app,
    classify_tool_use_agent,
    cmd_score,
    render_cost_report,
    render_first_call_tool_report,
    render_groundedness_report,
    render_refusal_report,
    render_termination_report,
    score_cost,
    score_first_call_tool,
    score_groundedness,
    score_refusal,
    score_termination,
)

_repo.ensure_build_imports_on_path()


# ---------------------------------------------------------------------------
# Helpers shared across the suite
# ---------------------------------------------------------------------------


def _make_envelope(
    tmp_path: Path,
    queries_tiny_path: Path,
    *trace_paths: Path,
) -> Path:
    result = ingest(queries_tiny_path, list(trace_paths))
    env = tmp_path / "ingested.jsonl"
    _write_normalized(env, result)
    return env


@pytest.fixture
def envelope_path(
    tmp_path: Path,
    queries_tiny_path: Path,
    traces_rag_path: Path,
    traces_tua_path: Path,
) -> Path:
    return _make_envelope(tmp_path, queries_tiny_path, traces_rag_path, traces_tua_path)


# ---------------------------------------------------------------------------
# Constants + rubric registration
# ---------------------------------------------------------------------------


def test_all_rubrics_lock():
    assert ALL_RUBRICS == (
        "refusal",
        "groundedness",
        "first_call_tool",
        "termination",
        "cost",
    )


def test_rubric_alias_for_slice3_callers():
    """The legacy RUBRIC constant equals RUBRIC_REFUSAL — slice-3 callers
    that imported `RUBRIC` keep working."""
    assert RUBRIC == RUBRIC_REFUSAL == "refusal"


def test_schema_constants():
    assert SCHEMA_RAG_APP == "rag-app.ask.v1"
    assert SCHEMA_TOOL_USE_AGENT == "tool-use-agent.ask.v1"


# ---------------------------------------------------------------------------
# _read_envelope
# ---------------------------------------------------------------------------


def test_read_envelope_splits_labels_and_traces(envelope_path):
    labels, traces = _read_envelope(envelope_path)
    assert len(labels) == 3
    assert len(traces) == 5


def test_read_envelope_rejects_bad_json(tmp_path: Path):
    p = tmp_path / "env.jsonl"
    p.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ScoreError, match="invalid JSON"):
        _read_envelope(p)


def test_read_envelope_rejects_missing_kind_or_record(tmp_path: Path):
    p = tmp_path / "env.jsonl"
    p.write_text('{"kind": "label"}\n', encoding="utf-8")
    with pytest.raises(ScoreError, match="envelope must have keys"):
        _read_envelope(p)


def test_read_envelope_rejects_unknown_kind(tmp_path: Path):
    p = tmp_path / "env.jsonl"
    p.write_text('{"kind": "mystery", "record": {}}\n', encoding="utf-8")
    with pytest.raises(ScoreError, match="unknown envelope kind"):
        _read_envelope(p)


def test_read_envelope_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "env.jsonl"
    p.write_text(
        '{"kind": "label", "record": {"id": "x"}}\n\n\n', encoding="utf-8"
    )
    labels, traces = _read_envelope(p)
    assert len(labels) == 1
    assert traces == []


# ---------------------------------------------------------------------------
# classify_rag_app
# ---------------------------------------------------------------------------


def test_classify_rag_app_refused_low_score():
    trace = {"mode": "refused-low-score"}
    assert classify_rag_app(trace) == OBSERVED_REFUSE


def test_classify_rag_app_dry_run_is_no_observation():
    assert classify_rag_app({"mode": "dry-run"}) == OBSERVED_NONE


def test_classify_rag_app_live_refusal_text(minimal_rag_trace):
    from rag_app.verify import REFUSAL_SENTENCE

    minimal_rag_trace["answer"]["text"] = REFUSAL_SENTENCE
    assert classify_rag_app(minimal_rag_trace) == OBSERVED_REFUSE


def test_classify_rag_app_live_answer(minimal_rag_trace):
    assert classify_rag_app(minimal_rag_trace) == OBSERVED_ANSWER


def test_classify_rag_app_missing_answer_block():
    trace = {"mode": "live"}
    assert classify_rag_app(trace) == OBSERVED_NONE


def test_classify_rag_app_non_string_text():
    trace = {"mode": "live", "answer": {"text": None}}
    assert classify_rag_app(trace) == OBSERVED_NONE


# ---------------------------------------------------------------------------
# classify_tool_use_agent
# ---------------------------------------------------------------------------


def test_classify_tua_dry_run_is_no_observation():
    assert classify_tool_use_agent({"mode": "dry-run"}) == OBSERVED_NONE


def test_classify_tua_live_answer(minimal_tua_trace):
    assert classify_tool_use_agent(minimal_tua_trace) == OBSERVED_ANSWER


def test_classify_tua_live_refusal(minimal_tua_trace):
    from tool_use_agent.verify import REFUSAL_SENTENCE

    minimal_tua_trace["final_text"] = REFUSAL_SENTENCE
    minimal_tua_trace["refusal_reason"] = "model_refused"
    assert classify_tool_use_agent(minimal_tua_trace) == OBSERVED_REFUSE


def test_classify_tua_disagreement_raises(minimal_tua_trace):
    """Text says refused but refusal_reason is null → ScoreError."""
    from tool_use_agent.verify import REFUSAL_SENTENCE

    minimal_tua_trace["final_text"] = REFUSAL_SENTENCE
    minimal_tua_trace["refusal_reason"] = None
    with pytest.raises(ScoreError, match="disagree"):
        classify_tool_use_agent(minimal_tua_trace)


def test_classify_tua_disagreement_other_direction(minimal_tua_trace):
    """Text is an answer but refusal_reason is set → ScoreError."""
    minimal_tua_trace["final_text"] = "All good"
    minimal_tua_trace["refusal_reason"] = "model_refused"
    with pytest.raises(ScoreError, match="disagree"):
        classify_tool_use_agent(minimal_tua_trace)


def test_classify_tua_empty_final_text():
    trace = {"mode": "live", "final_text": ""}
    assert classify_tool_use_agent(trace) == OBSERVED_NONE


def test_classify_dispatches_by_schema(minimal_rag_trace, minimal_tua_trace):
    assert classify(minimal_rag_trace) == OBSERVED_ANSWER
    assert classify(minimal_tua_trace) == OBSERVED_ANSWER


def test_classify_unknown_schema_raises():
    with pytest.raises(ScoreError, match="unknown schema_version"):
        classify({"schema_version": "made-up", "record_id": "x"})


# ---------------------------------------------------------------------------
# Refusal rubric
# ---------------------------------------------------------------------------


def test_score_refusal_counts_paired_rows(envelope_path):
    result = score_refusal(envelope_path)
    # 3 labels, 5 traces; q-tiny-001 hits both builds (2 rows), q-tiny-002 hits
    # both (2 rows), q-tiny-003 hits TUA only (1 row) = 5 rows.
    assert len(result.rows) == 5
    assert result.n_labels == 3
    assert result.n_traces == 5
    assert result.n_unpaired_traces == 0
    assert result.n_unpaired_labels == 0


def test_score_refusal_match_logic(envelope_path):
    result = score_refusal(envelope_path)
    by_label = {(r.label_id, r.schema_version): r for r in result.rows}
    # q-tiny-001 is expected=answer; rag-001 answered, tua-001 answered → both match
    assert by_label[("q-tiny-001", SCHEMA_RAG_APP)].match is True
    assert by_label[("q-tiny-001", SCHEMA_TOOL_USE_AGENT)].match is True
    # q-tiny-002 is expected=refuse; rag-002 refused-low-score, tua-002 model_refused
    assert by_label[("q-tiny-002", SCHEMA_RAG_APP)].match is True
    assert by_label[("q-tiny-002", SCHEMA_TOOL_USE_AGENT)].match is True


def test_score_refusal_unpaired_trace(tmp_path: Path, queries_tiny_path):
    """A trace with a question that no label carries → unpaired_traces++."""
    orphan = tmp_path / "orphan.jsonl"
    orphan.write_text(
        json.dumps(
            {
                "schema_version": "rag-app.ask.v1",
                "record_id": "rag-orphan",
                "corpus_fingerprint": "x",
                "question": "Nobody labeled this",
                "mode": "live",
                "answer": {"text": "wat", "input_tokens": 1, "output_tokens": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, orphan)
    result = score_refusal(env)
    assert result.n_unpaired_traces == 1


def test_score_refusal_unpaired_label(tmp_path: Path, queries_tiny_path):
    """No traces → every label is unpaired."""
    env = _make_envelope(tmp_path, queries_tiny_path)  # no traces
    result = score_refusal(env)
    assert result.n_unpaired_labels == 3


def test_score_refusal_rows_sort_stable(envelope_path):
    result = score_refusal(envelope_path)
    keys = [(r.schema_version, r.record_id, r.label_id) for r in result.rows]
    assert keys == sorted(keys)


def test_render_refusal_report_table_shape(envelope_path):
    result = score_refusal(envelope_path)
    md = render_refusal_report(result)
    assert "# Refusal rubric" in md
    assert "labels=3" in md
    assert "traces=5" in md
    assert "| build | expected" in md
    assert "rag-app.ask.v1" in md
    assert "tool-use-agent.ask.v1" in md
    assert "overall" in md


def test_render_refusal_report_empty():
    from evals_harness.score import ScoreResult

    md = render_refusal_report(ScoreResult())
    assert "nothing to score" in md


# ---------------------------------------------------------------------------
# Groundedness rubric
# ---------------------------------------------------------------------------


def test_extract_groundedness_missing_verification():
    outcome, total, resolved, all_res, src = _extract_groundedness({}, None)
    assert outcome == GROUNDED_NONE
    assert total == 0
    assert resolved == 0
    assert all_res is False
    assert src is False


def test_extract_groundedness_all_resolved_no_expected_source(minimal_rag_trace):
    outcome, *_ = _extract_groundedness(minimal_rag_trace, None)
    assert outcome == GROUNDED_TRUE


def test_extract_groundedness_all_resolved_expected_source_cited(minimal_rag_trace):
    outcome, _, _, _, src_cited = _extract_groundedness(minimal_rag_trace, "DECISIONS.md")
    assert outcome == GROUNDED_TRUE
    assert src_cited is True


def test_extract_groundedness_all_resolved_expected_source_NOT_cited(minimal_rag_trace):
    outcome, _, _, _, src_cited = _extract_groundedness(minimal_rag_trace, "OBJECTIVE.md")
    assert outcome == GROUNDED_FALSE
    assert src_cited is False


def test_extract_groundedness_not_all_resolved():
    trace = {
        "verification": {
            "total": 2,
            "resolved": 1,
            "all_resolved": False,
            "citations": [],
        }
    }
    outcome, total, resolved, *_ = _extract_groundedness(trace, None)
    assert outcome == GROUNDED_FALSE
    assert total == 2
    assert resolved == 1


def test_score_groundedness_runs_only_on_rag(envelope_path):
    result = score_groundedness(envelope_path)
    # Only q-tiny-001 is (answer, rag-app, applies_to has rag-app).
    # rag-002 is refuse-shape; its label q-tiny-002 has expected_outcome=refuse so it's filtered out.
    schemas = {r.schema_version for r in result.rows}
    assert schemas == {SCHEMA_RAG_APP}


def test_score_groundedness_eligible_labels(envelope_path):
    result = score_groundedness(envelope_path)
    # 1 eligible label: q-tiny-001 (answer + rag-app in applies_to).
    assert result.n_labels == 1
    # eligible_traces is the count of rag-app traces seen (2: rag-001, rag-002).
    assert result.n_traces == 2


def test_score_groundedness_marks_match(envelope_path):
    result = score_groundedness(envelope_path)
    rag_row = next(r for r in result.rows if r.label_id == "q-tiny-001")
    assert rag_row.match is True
    assert rag_row.observed_outcome == GROUNDED_TRUE
    assert rag_row.citations_total == 1
    assert rag_row.citations_resolved == 1


def test_score_groundedness_unpaired_when_no_label(tmp_path: Path, queries_tiny_path):
    """A rag-app trace with a question not in any answer-label."""
    orphan = tmp_path / "orphan.jsonl"
    orphan.write_text(
        json.dumps(
            {
                "schema_version": "rag-app.ask.v1",
                "record_id": "rag-orphan",
                "corpus_fingerprint": "x",
                "question": "Nobody labeled this",
                "mode": "live",
                "answer": {"text": "x", "input_tokens": 1, "output_tokens": 1},
                "verification": {"total": 1, "resolved": 1, "all_resolved": True, "citations": []},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, orphan)
    result = score_groundedness(env)
    assert result.n_unpaired_traces == 1


def test_render_groundedness_empty():
    from evals_harness.score import GroundednessResult

    md = render_groundedness_report(GroundednessResult())
    assert "# Groundedness rubric" in md
    assert "nothing to score" in md


def test_render_groundedness_report_with_failures(tmp_path: Path, queries_tiny_path):
    """Synthetic trace whose verification fails the rubric → 'Not-grounded rows:'."""
    trace = tmp_path / "rag_failing.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "rag-app.ask.v1",
                "record_id": "rag-fail",
                "corpus_fingerprint": "ff00ff00ff00ff00",
                "question": "What is the canonical refusal sentence?",
                "mode": "live",
                "answer": {"text": "x", "input_tokens": 1, "output_tokens": 1},
                "verification": {
                    "total": 2,
                    "resolved": 1,
                    "all_resolved": False,
                    "citations": [{"source": "X.md", "resolved": False}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_groundedness(env)
    md = render_groundedness_report(result)
    assert "Not-grounded rows:" in md
    assert "q-tiny-001" in md


# ---------------------------------------------------------------------------
# First-call tool rubric
# ---------------------------------------------------------------------------


def test_extract_first_tool_present():
    trace = {"tool_calls": [{"tool": "grep_repo", "input": {}}]}
    assert _extract_first_tool(trace) == "grep_repo"


def test_extract_first_tool_empty_list():
    assert _extract_first_tool({"tool_calls": []}) is None


def test_extract_first_tool_missing_field():
    assert _extract_first_tool({}) is None


def test_extract_first_tool_non_list():
    assert _extract_first_tool({"tool_calls": {"oops": 1}}) is None


def test_extract_first_tool_non_dict_first_call():
    assert _extract_first_tool({"tool_calls": ["a-string"]}) is None


def test_extract_first_tool_non_string_name():
    assert _extract_first_tool({"tool_calls": [{"tool": 42}]}) is None


def test_score_first_call_tool_match(envelope_path):
    """q-tiny-001 expects read_repo_file as first tool, tua-001's first call
    is read_repo_file → match. q-tiny-003 expects list_pipeline_rows, tua-003's
    first call is list_pipeline_rows → match."""
    result = score_first_call_tool(envelope_path)
    by_label = {r.label_id: r for r in result.rows}
    assert by_label["q-tiny-001"].observed_outcome == FIRST_CALL_MATCH
    assert by_label["q-tiny-001"].match is True
    assert by_label["q-tiny-003"].observed_outcome == FIRST_CALL_MATCH


def test_score_first_call_tool_no_observation(tmp_path: Path, queries_tiny_path):
    """A TUA trace with empty tool_calls → no_observation."""
    trace = tmp_path / "tua_no_calls.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "tua-empty",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "What is the canonical refusal sentence?",
                "mode": "live",
                "final_text": "answered without tools",
                "refusal_reason": None,
                "stop_reason": "end_turn",
                "steps_taken": 0,
                "max_steps": 6,
                "input_tokens": 10,
                "output_tokens": 5,
                "tool_calls": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_first_call_tool(env)
    row = next(r for r in result.rows if r.label_id == "q-tiny-001")
    assert row.observed_outcome == FIRST_CALL_NONE
    assert row.match is False


def test_score_first_call_tool_mismatch(tmp_path: Path, queries_tiny_path):
    trace = tmp_path / "tua_wrong_tool.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "tua-wrong",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "What is the canonical refusal sentence?",
                "mode": "live",
                "final_text": "answered",
                "refusal_reason": None,
                "stop_reason": "end_turn",
                "steps_taken": 1,
                "max_steps": 6,
                "input_tokens": 10,
                "output_tokens": 5,
                "tool_calls": [{"tool": "count_by_stage", "input": {}, "latency_ms": 1}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_first_call_tool(env)
    row = next(r for r in result.rows if r.label_id == "q-tiny-001")
    assert row.observed_outcome == FIRST_CALL_MISMATCH
    assert row.match is False


def test_score_first_call_tool_unpaired_when_no_label(tmp_path: Path, queries_tiny_path):
    """A TUA trace whose question has no label with expected_first_tool set."""
    trace = tmp_path / "tua_orphan.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "tua-orphan",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "Nobody labeled this",
                "mode": "live",
                "final_text": "x",
                "refusal_reason": None,
                "stop_reason": "end_turn",
                "steps_taken": 0,
                "max_steps": 6,
                "input_tokens": 1,
                "output_tokens": 1,
                "tool_calls": [{"tool": "grep_repo", "input": {}, "latency_ms": 1}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_first_call_tool(env)
    assert result.n_unpaired_traces == 1


def test_render_first_call_tool_empty():
    from evals_harness.score import FirstCallToolResult

    md = render_first_call_tool_report(FirstCallToolResult())
    assert "# First-call tool rubric" in md
    assert "nothing to score" in md


def test_render_first_call_tool_report_with_failures(tmp_path: Path, queries_tiny_path):
    """Force a mismatch so the 'Mismatches' section appears."""
    trace = tmp_path / "tua_mismatch.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "tua-mm",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "What is the canonical refusal sentence?",
                "mode": "live",
                "final_text": "x",
                "refusal_reason": None,
                "stop_reason": "end_turn",
                "steps_taken": 1,
                "max_steps": 6,
                "input_tokens": 1,
                "output_tokens": 1,
                "tool_calls": [{"tool": "grep_repo", "input": {}, "latency_ms": 1}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_first_call_tool(env)
    md = render_first_call_tool_report(result)
    assert "Mismatches" in md


# ---------------------------------------------------------------------------
# Termination rubric
# ---------------------------------------------------------------------------


def test_extract_termination_dry_run_is_no_observation():
    outcome, *_ = _extract_termination({"mode": "dry-run"})
    assert outcome == TERMINATION_NONE


def test_extract_termination_clean_end_turn(minimal_tua_trace):
    outcome, stop, refusal, steps, max_steps = _extract_termination(minimal_tua_trace)
    assert outcome == TERMINATION_CLEAN
    assert stop == "end_turn"
    assert refusal is None
    assert steps == 2
    assert max_steps == 6


def test_extract_termination_refusal_model_refused():
    trace = {
        "mode": "live",
        "stop_reason": "end_turn",
        "refusal_reason": "model_refused",
        "steps_taken": 1,
        "max_steps": 6,
    }
    outcome, *_ = _extract_termination(trace)
    assert outcome == TERMINATION_MODEL_REFUSED


def test_extract_termination_max_steps_exhausted():
    trace = {
        "mode": "live",
        "stop_reason": "tool_use",
        "refusal_reason": "max_steps_exhausted",
        "steps_taken": 6,
        "max_steps": 6,
    }
    outcome, *_ = _extract_termination(trace)
    assert outcome == TERMINATION_MAX_STEPS


def test_extract_termination_repeated_tool_error():
    trace = {
        "mode": "live",
        "stop_reason": "tool_use",
        "refusal_reason": "repeated_tool_error",
        "steps_taken": 3,
        "max_steps": 6,
    }
    outcome, *_ = _extract_termination(trace)
    assert outcome == TERMINATION_REPEATED_ERROR


def test_extract_termination_unknown_refusal_reason_raises():
    trace = {
        "mode": "live",
        "stop_reason": "end_turn",
        "refusal_reason": "novel-bucket",
        "record_id": "x",
    }
    with pytest.raises(ScoreError, match="unknown refusal_reason"):
        _extract_termination(trace)


def test_extract_termination_no_refusal_but_non_end_turn_raises():
    trace = {
        "mode": "live",
        "stop_reason": "tool_use",
        "refusal_reason": None,
        "record_id": "x",
    }
    with pytest.raises(ScoreError, match="build contract violation"):
        _extract_termination(trace)


def test_extract_termination_non_int_steps_become_none():
    trace = {
        "mode": "live",
        "stop_reason": "end_turn",
        "refusal_reason": None,
        "steps_taken": "two",
        "max_steps": None,
    }
    outcome, _, _, steps, max_steps = _extract_termination(trace)
    assert outcome == TERMINATION_CLEAN
    assert steps is None
    assert max_steps is None


def test_score_termination_runs_only_on_tua(envelope_path):
    result = score_termination(envelope_path)
    schemas = {r.schema_version for r in result.rows}
    assert schemas == {SCHEMA_TOOL_USE_AGENT}


def test_score_termination_eligible_labels(envelope_path):
    result = score_termination(envelope_path)
    # Eligible: TUA + expected_outcome=answer. q-tiny-001 (rag+tua, answer),
    # q-tiny-003 (tua-only, answer) qualify. q-tiny-002 is refuse-shape.
    assert result.n_labels == 2


def test_score_termination_rows_match_only_ended_clean(envelope_path):
    result = score_termination(envelope_path)
    for r in result.rows:
        assert r.match == (r.observed_outcome == TERMINATION_CLEAN)


def test_score_termination_unpaired_when_no_answer_label(tmp_path: Path, queries_tiny_path):
    """A TUA trace whose question has no answer-shaped label → unpaired."""
    trace = tmp_path / "tua_unpaired.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "tua-up",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "Nobody labeled this",
                "mode": "live",
                "final_text": "x",
                "refusal_reason": None,
                "stop_reason": "end_turn",
                "steps_taken": 0,
                "max_steps": 6,
                "input_tokens": 1,
                "output_tokens": 1,
                "tool_calls": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_termination(env)
    assert result.n_unpaired_traces == 1


def test_render_termination_empty():
    from evals_harness.score import TerminationResult

    md = render_termination_report(TerminationResult())
    assert "# Termination rubric" in md
    assert "nothing to score" in md


def test_render_termination_report_with_failures(tmp_path: Path, queries_tiny_path):
    """Non-clean termination should land in the per-row failures section."""
    trace = tmp_path / "tua_max_steps.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "tua-ms",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "What is the canonical refusal sentence?",
                "mode": "live",
                "final_text": "x",
                "refusal_reason": "max_steps_exhausted",
                "stop_reason": "tool_use",
                "steps_taken": 6,
                "max_steps": 6,
                "input_tokens": 1,
                "output_tokens": 1,
                "tool_calls": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    result = score_termination(env)
    md = render_termination_report(result)
    assert "Non-clean terminations:" in md
    assert "max_steps_exhausted" in md


# ---------------------------------------------------------------------------
# Cost rubric
# ---------------------------------------------------------------------------


def test_extract_cost_rag_app_dry_run():
    outcome, inp, out = _extract_cost_rag_app({"mode": "dry-run"})
    assert outcome == COST_NONE
    assert inp is None and out is None


def test_extract_cost_rag_app_observed(minimal_rag_trace):
    outcome, inp, out = _extract_cost_rag_app(minimal_rag_trace)
    assert outcome == COST_OBSERVED
    assert inp == 120 and out == 30


def test_extract_cost_rag_app_missing_answer_block():
    outcome, inp, out = _extract_cost_rag_app({"mode": "live"})
    assert outcome == COST_NONE


def test_extract_cost_rag_app_non_int_tokens():
    trace = {"mode": "live", "answer": {"text": "x", "input_tokens": "1", "output_tokens": 1}}
    outcome, *_ = _extract_cost_rag_app(trace)
    assert outcome == COST_NONE


def test_extract_cost_tua_observed(minimal_tua_trace):
    outcome, inp, out, steps, max_steps, lat = _extract_cost_tool_use_agent(minimal_tua_trace)
    assert outcome == COST_OBSERVED
    assert inp == 200 and out == 50
    assert steps == 2 and max_steps == 6
    assert lat == 12 + 18


def test_extract_cost_tua_dry_run():
    outcome, *_ = _extract_cost_tool_use_agent({"mode": "dry-run"})
    assert outcome == COST_NONE


def test_extract_cost_tua_missing_tokens():
    trace = {"mode": "live", "tool_calls": []}
    outcome, *_ = _extract_cost_tool_use_agent(trace)
    assert outcome == COST_NONE


def test_extract_cost_tua_non_int_latency():
    trace = {
        "mode": "live",
        "input_tokens": 1,
        "output_tokens": 1,
        "steps_taken": 1,
        "max_steps": 2,
        "tool_calls": [
            {"tool": "x", "latency_ms": "fast"},
            {"tool": "y", "latency_ms": 5},
            "not-a-dict",
        ],
    }
    outcome, _, _, _, _, lat = _extract_cost_tool_use_agent(trace)
    assert outcome == COST_OBSERVED
    assert lat == 5  # only the int latency contributes


def test_score_cost_both_builds(envelope_path):
    result = score_cost(envelope_path)
    schemas = {r.schema_version for r in result.rows}
    assert schemas == {SCHEMA_RAG_APP, SCHEMA_TOOL_USE_AGENT}


def test_score_cost_observable_vs_none(envelope_path):
    result = score_cost(envelope_path)
    # rag-001 live (observed), rag-002 refused-low-score (none), all three tua live (observed).
    by_id = {r.record_id: r for r in result.rows}
    assert by_id["rag-001"].observed_outcome == COST_OBSERVED
    assert by_id["rag-002"].observed_outcome == COST_NONE
    assert by_id["tua-001"].observed_outcome == COST_OBSERVED


def test_score_cost_total_tokens_calculated(envelope_path):
    result = score_cost(envelope_path)
    by_id = {r.record_id: r for r in result.rows}
    assert by_id["rag-001"].total_tokens == 110 + 25
    assert by_id["tua-001"].total_tokens == 200 + 40


def test_score_cost_unpaired_trace(tmp_path: Path, queries_tiny_path):
    orphan = tmp_path / "orphan.jsonl"
    orphan.write_text(
        json.dumps(
            {
                "schema_version": "rag-app.ask.v1",
                "record_id": "rag-orphan",
                "corpus_fingerprint": "x",
                "question": "Nobody labeled this",
                "mode": "live",
                "answer": {"text": "wat", "input_tokens": 1, "output_tokens": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, orphan)
    result = score_cost(env)
    assert result.n_unpaired_traces == 1


def test_render_cost_empty():
    from evals_harness.score import CostResult

    md = render_cost_report(CostResult())
    assert "# Cost rubric" in md
    assert "nothing to score" in md


def test_render_cost_with_data(envelope_path):
    result = score_cost(envelope_path)
    md = render_cost_report(result)
    assert "# Cost rubric" in md
    assert "total_tokens p50" in md
    # TUA-only extras section should appear since TUA has observed rows.
    assert "steps_taken p50" in md
    assert "tool_latency_ms_sum p50" in md


# ---------------------------------------------------------------------------
# Percentile helpers
# ---------------------------------------------------------------------------


def test_percentile_empty():
    assert _percentile([], 50.0) == 0


def test_percentile_single():
    assert _percentile([42], 50.0) == 42


def test_percentile_p0_returns_min():
    assert _percentile([1, 2, 3, 4, 5], 0) == 1


def test_percentile_p100_returns_max():
    assert _percentile([1, 2, 3, 4, 5], 100) == 5


def test_percentile_interpolates():
    # 10, 20, 30, 40 — p50 is between idx 1 (20) and 2 (30) at frac 0.5 = 25
    assert _percentile([10, 20, 30, 40], 50.0) == 25


def test_cost_stats_empty():
    assert _cost_stats([]) == (0, 0, 0, 0)


def test_cost_stats_single():
    n, p50, p95, mx = _cost_stats([7])
    assert (n, p50, p95, mx) == (1, 7, 7, 7)


def test_cost_stats_full():
    n, p50, p95, mx = _cost_stats([1, 5, 10, 100])
    assert n == 4
    assert mx == 100


# ---------------------------------------------------------------------------
# cmd_score CLI dispatch
# ---------------------------------------------------------------------------


def _capture(fn, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = fn(*args, **kwargs)
    return rc, out.getvalue(), err.getvalue()


def test_cmd_score_refusal_writes_jsonl(envelope_path, tmp_path: Path):
    out_path = tmp_path / "scored.jsonl"
    md_path = tmp_path / "report.md"
    args = argparse.Namespace(
        rubric="refusal",
        ingested=str(envelope_path),
        out=str(out_path),
        markdown=str(md_path),
    )
    rc, stdout, _ = _capture(cmd_score, args)
    assert rc == 0
    assert out_path.is_file()
    assert md_path.is_file()
    assert "# Refusal rubric" in stdout
    rows = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    assert len(rows) == 5
    for row in rows:
        assert row["rubric"] == "refusal"
        assert "match" in row


def test_cmd_score_groundedness(envelope_path, tmp_path: Path):
    out_path = tmp_path / "g.jsonl"
    args = argparse.Namespace(
        rubric="groundedness",
        ingested=str(envelope_path),
        out=str(out_path),
        markdown=None,
    )
    rc, stdout, _ = _capture(cmd_score, args)
    assert rc == 0
    assert "Groundedness rubric" in stdout
    rows = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    for row in rows:
        assert row["rubric"] == "groundedness"


def test_cmd_score_first_call_tool(envelope_path, tmp_path: Path):
    out_path = tmp_path / "f.jsonl"
    args = argparse.Namespace(
        rubric="first_call_tool",
        ingested=str(envelope_path),
        out=str(out_path),
        markdown=None,
    )
    rc, _, _ = _capture(cmd_score, args)
    assert rc == 0
    rows = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    for row in rows:
        assert row["rubric"] == "first_call_tool"


def test_cmd_score_termination(envelope_path, tmp_path: Path):
    out_path = tmp_path / "t.jsonl"
    args = argparse.Namespace(
        rubric="termination",
        ingested=str(envelope_path),
        out=str(out_path),
        markdown=None,
    )
    rc, _, _ = _capture(cmd_score, args)
    assert rc == 0
    rows = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    for row in rows:
        assert row["rubric"] == "termination"


def test_cmd_score_cost(envelope_path, tmp_path: Path):
    out_path = tmp_path / "c.jsonl"
    args = argparse.Namespace(
        rubric="cost",
        ingested=str(envelope_path),
        out=str(out_path),
        markdown=None,
    )
    rc, _, _ = _capture(cmd_score, args)
    assert rc == 0
    rows = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    for row in rows:
        assert row["rubric"] == "cost"
        assert "total_tokens" in row


def test_cmd_score_no_out_still_prints(envelope_path):
    args = argparse.Namespace(
        rubric="refusal",
        ingested=str(envelope_path),
        out=None,
        markdown=None,
    )
    rc, stdout, _ = _capture(cmd_score, args)
    assert rc == 0
    assert "Refusal rubric" in stdout


def test_cmd_score_unknown_rubric_returns_2(envelope_path):
    args = argparse.Namespace(
        rubric="nonsense",
        ingested=str(envelope_path),
        out=None,
        markdown=None,
    )
    rc, _, stderr = _capture(cmd_score, args)
    assert rc == 2
    assert "unknown rubric" in stderr


def test_cmd_score_returns_2_on_invariant_drift(envelope_path, monkeypatch):
    import tool_use_agent.verify as tua_verify

    monkeypatch.setattr(tua_verify, "REFUSAL_SENTENCE", "drifted")
    args = argparse.Namespace(
        rubric="refusal",
        ingested=str(envelope_path),
        out=None,
        markdown=None,
    )
    rc, _, stderr = _capture(cmd_score, args)
    assert rc == 2
    assert "INVARIANT FAILED" in stderr


def test_cmd_score_returns_2_on_score_error(tmp_path: Path, queries_tiny_path):
    """A trace where final_text==refusal but refusal_reason is null triggers
    ScoreError during refusal classification."""
    from rag_app.verify import REFUSAL_SENTENCE

    trace = tmp_path / "bad.jsonl"
    trace.write_text(
        json.dumps(
            {
                "schema_version": "tool-use-agent.ask.v1",
                "record_id": "bad",
                "corpus_fingerprint": "aa11aa11aa11aa11",
                "question": "What is the canonical refusal sentence?",
                "mode": "live",
                "final_text": REFUSAL_SENTENCE,
                "refusal_reason": None,  # disagreement
                "stop_reason": "end_turn",
                "steps_taken": 0,
                "max_steps": 6,
                "input_tokens": 1,
                "output_tokens": 1,
                "tool_calls": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = _make_envelope(tmp_path, queries_tiny_path, trace)
    args = argparse.Namespace(
        rubric="refusal",
        ingested=str(env),
        out=None,
        markdown=None,
    )
    rc, _, stderr = _capture(cmd_score, args)
    assert rc == 2
    assert "SCORE FAILED" in stderr
