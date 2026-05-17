"""Tests for evals_harness.ingest: label + trace validation and CLI."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from evals_harness import ingest as ing
from evals_harness.ingest import (
    IngestError,
    IngestResult,
    KNOWN_SCHEMAS,
    LABEL_KEYS,
    OUTCOME_VOCAB,
    REQUIRED_TRACE_FIELDS,
    SHAPE_VOCAB,
    _read_jsonl,
    _write_normalized,
    cmd_ingest,
    ingest,
    validate_label,
    validate_trace,
)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_known_schemas_lock():
    assert KNOWN_SCHEMAS == frozenset({"rag-app.ask.v1", "tool-use-agent.ask.v1"})


def test_label_keys_lock_is_9_named_fields():
    assert len(LABEL_KEYS) == 9
    assert "id" in LABEL_KEYS
    assert "corpus_fingerprint_at_label" in LABEL_KEYS


def test_shape_vocab_lock():
    assert SHAPE_VOCAB == frozenset(
        {"in_corpus", "out_of_corpus", "tracker_rollup", "adversarial_in_corpus"}
    )


def test_outcome_vocab_lock():
    assert OUTCOME_VOCAB == frozenset({"answer", "refuse"})


def test_required_trace_fields():
    assert "schema_version" in REQUIRED_TRACE_FIELDS
    assert "record_id" in REQUIRED_TRACE_FIELDS
    assert "corpus_fingerprint" in REQUIRED_TRACE_FIELDS
    assert "question" in REQUIRED_TRACE_FIELDS


# ---------------------------------------------------------------------------
# _read_jsonl
# ---------------------------------------------------------------------------


def test_read_jsonl_strips_blank_lines(tmp_path: Path):
    p = tmp_path / "f.jsonl"
    p.write_text('{"a": 1}\n\n\n{"b": 2}\n', encoding="utf-8")
    recs = _read_jsonl(p)
    assert recs == [{"a": 1}, {"b": 2}]


def test_read_jsonl_raises_on_bad_json(tmp_path: Path):
    p = tmp_path / "f.jsonl"
    p.write_text('{"ok": true}\n{not json}\n', encoding="utf-8")
    with pytest.raises(IngestError, match="invalid JSON"):
        _read_jsonl(p)


def test_read_jsonl_raises_on_non_object_record(tmp_path: Path):
    p = tmp_path / "f.jsonl"
    p.write_text('"a string is not an object"\n', encoding="utf-8")
    with pytest.raises(IngestError, match="record must be a JSON object"):
        _read_jsonl(p)


# ---------------------------------------------------------------------------
# validate_label
# ---------------------------------------------------------------------------


def test_validate_label_accepts_canonical(minimal_label):
    validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_extra_key(minimal_label):
    minimal_label["extra"] = "boom"
    with pytest.raises(IngestError, match="extra="):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_missing_key(minimal_label):
    del minimal_label["notes"]
    with pytest.raises(IngestError, match="missing="):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_unknown_shape(minimal_label):
    minimal_label["shape"] = "nonsense"
    with pytest.raises(IngestError, match="shape="):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_unknown_outcome(minimal_label):
    minimal_label["expected_outcome"] = "maybe"
    with pytest.raises(IngestError, match="expected_outcome="):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_empty_applies_to(minimal_label):
    minimal_label["applies_to"] = []
    minimal_label["corpus_fingerprint_at_label"] = {}
    with pytest.raises(IngestError, match="applies_to must be a non-empty list"):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_non_list_applies_to(minimal_label):
    minimal_label["applies_to"] = "rag-app.ask.v1"
    with pytest.raises(IngestError, match="applies_to must be a non-empty list"):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_unknown_schema_in_applies_to(minimal_label):
    minimal_label["applies_to"] = ["bogus.ask.v9"]
    minimal_label["corpus_fingerprint_at_label"] = {"bogus.ask.v9": "x" * 16}
    with pytest.raises(IngestError, match="unknown schema"):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_non_dict_fingerprints(minimal_label):
    minimal_label["corpus_fingerprint_at_label"] = ["not", "a", "dict"]
    with pytest.raises(IngestError, match="corpus_fingerprint_at_label must be a"):
        validate_label(minimal_label, Path("f"), 1)


def test_validate_label_rejects_fingerprint_key_mismatch(minimal_label):
    minimal_label["corpus_fingerprint_at_label"] = {"rag-app.ask.v1": "x" * 16}
    # applies_to lists both schemas but fingerprints only one.
    with pytest.raises(IngestError, match="corpus_fingerprint_at_label keys"):
        validate_label(minimal_label, Path("f"), 1)


# ---------------------------------------------------------------------------
# validate_trace
# ---------------------------------------------------------------------------


def test_validate_trace_accepts_canonical(minimal_rag_trace):
    validate_trace(minimal_rag_trace, Path("t"), 1)


def test_validate_trace_rejects_missing_field(minimal_rag_trace):
    del minimal_rag_trace["question"]
    with pytest.raises(IngestError, match="missing required field"):
        validate_trace(minimal_rag_trace, Path("t"), 1)


def test_validate_trace_rejects_unknown_schema(minimal_rag_trace):
    minimal_rag_trace["schema_version"] = "rag-app.ask.v9"
    with pytest.raises(IngestError, match="schema_version="):
        validate_trace(minimal_rag_trace, Path("t"), 1)


# ---------------------------------------------------------------------------
# ingest() integration
# ---------------------------------------------------------------------------


def test_ingest_happy_path(queries_tiny_path, traces_rag_path, traces_tua_path):
    result = ingest(queries_tiny_path, [traces_rag_path, traces_tua_path])
    assert isinstance(result, IngestResult)
    assert len(result.labels) == 3
    assert len(result.traces) == 5  # 2 rag + 3 tua
    assert len(result.invariants) == 2


def test_ingest_runs_invariants_before_validation(queries_tiny_path, tmp_path: Path, monkeypatch):
    """If startup invariants fail, ingest must raise — it should never proceed
    to schema validation when the cross-build pin is broken."""
    import tool_use_agent.verify as tua_verify

    monkeypatch.setattr(tua_verify, "REFUSAL_SENTENCE", "drifted")
    from evals_harness.invariants import InvariantError

    with pytest.raises(InvariantError):
        ingest(queries_tiny_path, [])


def test_ingest_rejects_malformed_label(tmp_path: Path, traces_rag_path, minimal_label):
    bad_label = dict(minimal_label)
    bad_label["shape"] = "nonsense"
    p = tmp_path / "labels.jsonl"
    p.write_text(json.dumps(bad_label) + "\n", encoding="utf-8")
    with pytest.raises(IngestError, match="shape="):
        ingest(p, [])


def test_ingest_rejects_malformed_trace(queries_tiny_path, tmp_path: Path):
    bad = {
        "schema_version": "rag-app.ask.v1",
        "record_id": "x",
        "corpus_fingerprint": "y",
        # missing "question"
    }
    p = tmp_path / "traces.jsonl"
    p.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    with pytest.raises(IngestError, match="missing required field"):
        ingest(queries_tiny_path, [p])


# ---------------------------------------------------------------------------
# _write_normalized
# ---------------------------------------------------------------------------


def test_write_normalized_emits_envelope(
    queries_tiny_path, traces_rag_path, traces_tua_path, tmp_path: Path
):
    result = ingest(queries_tiny_path, [traces_rag_path, traces_tua_path])
    out = tmp_path / "nested" / "ingested.jsonl"
    _write_normalized(out, result)
    assert out.is_file()
    lines = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    kinds = [line["kind"] for line in lines]
    assert kinds.count("label") == 3
    assert kinds.count("trace") == 5
    label_line = next(line for line in lines if line["kind"] == "label")
    assert set(label_line.keys()) == {"kind", "id", "applies_to", "record"}
    trace_line = next(line for line in lines if line["kind"] == "trace")
    assert set(trace_line.keys()) == {"kind", "schema_version", "record_id", "record"}


def test_write_normalized_creates_parent_dirs(
    queries_tiny_path, tmp_path: Path
):
    result = ingest(queries_tiny_path, [])
    out = tmp_path / "a" / "b" / "c" / "ingested.jsonl"
    _write_normalized(out, result)
    assert out.is_file()


# ---------------------------------------------------------------------------
# cmd_ingest CLI dispatch
# ---------------------------------------------------------------------------


def _capture_stdout(fn, *args, **kwargs) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = fn(*args, **kwargs)
    return rc, out.getvalue(), err.getvalue()


def test_cmd_ingest_validates_only_when_no_out(
    queries_tiny_path, traces_rag_path
):
    args = argparse.Namespace(
        labels=str(queries_tiny_path),
        traces=[str(traces_rag_path)],
        out=None,
        verbose=False,
    )
    rc, stdout, stderr = _capture_stdout(cmd_ingest, args)
    assert rc == 0
    assert "traces, " in stdout
    assert "labels" in stdout
    assert "invariant checks passed" in stdout


def test_cmd_ingest_writes_envelope_when_out_set(
    queries_tiny_path, traces_rag_path, tmp_path: Path
):
    out_path = tmp_path / "ingested.jsonl"
    args = argparse.Namespace(
        labels=str(queries_tiny_path),
        traces=[str(traces_rag_path)],
        out=str(out_path),
        verbose=False,
    )
    rc, stdout, _ = _capture_stdout(cmd_ingest, args)
    assert rc == 0
    assert out_path.is_file()


def test_cmd_ingest_verbose_prints_per_invariant(queries_tiny_path):
    args = argparse.Namespace(
        labels=str(queries_tiny_path),
        traces=[],
        out=None,
        verbose=True,
    )
    rc, stdout, _ = _capture_stdout(cmd_ingest, args)
    assert rc == 0
    assert "ok: refusal_sentence_byte_equal" in stdout
    assert "ok: trace_helpers_behavior_equivalent" in stdout


def test_cmd_ingest_returns_2_on_ingest_error(tmp_path: Path):
    p = tmp_path / "labels.jsonl"
    p.write_text('{"not": "a-label"}\n', encoding="utf-8")
    args = argparse.Namespace(
        labels=str(p),
        traces=[],
        out=None,
        verbose=False,
    )
    rc, stdout, stderr = _capture_stdout(cmd_ingest, args)
    assert rc == 2
    assert "INGEST FAILED" in stderr


def test_cmd_ingest_returns_2_on_invariant_error(queries_tiny_path, monkeypatch):
    import tool_use_agent.verify as tua_verify

    monkeypatch.setattr(tua_verify, "REFUSAL_SENTENCE", "drifted")
    args = argparse.Namespace(
        labels=str(queries_tiny_path),
        traces=[],
        out=None,
        verbose=False,
    )
    rc, stdout, stderr = _capture_stdout(cmd_ingest, args)
    assert rc == 2
    assert "INVARIANT FAILED" in stderr
