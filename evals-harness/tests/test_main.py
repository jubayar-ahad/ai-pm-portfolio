"""Tests for evals_harness.__main__: argparse surface + dispatch."""

from __future__ import annotations


import pytest

from evals_harness.__main__ import _build_parser, main


def test_build_parser_returns_parser():
    parser = _build_parser()
    assert parser.prog == "evals_harness"


def test_main_no_args_errors(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_main_help_exits_clean(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "ingest" in captured.out
    assert "score" in captured.out
    assert "report" in captured.out


def test_main_dispatches_ingest(queries_tiny_path, capsys):
    rc = main(["ingest", "--labels", str(queries_tiny_path), "--verbose"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "labels" in captured.out
    assert "ok: " in captured.out


def test_main_dispatches_score(
    queries_tiny_path, traces_rag_path, traces_tua_path, tmp_path, capsys
):
    """Ingest first to produce an envelope, then score-refusal."""
    env_path = tmp_path / "ingested.jsonl"
    rc = main(
        [
            "ingest",
            "--labels", str(queries_tiny_path),
            "--traces", str(traces_rag_path), str(traces_tua_path),
            "--out", str(env_path),
        ]
    )
    assert rc == 0
    capsys.readouterr()  # discard ingest stdout
    rc = main(
        ["score", "--rubric", "refusal", "--ingested", str(env_path)]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "# Refusal rubric" in captured.out


def test_main_dispatches_report(
    queries_tiny_path, traces_rag_path, traces_tua_path, tmp_path, capsys
):
    """Full pipeline through main(): ingest → score → report."""
    env_path = tmp_path / "ingested.jsonl"
    main([
        "ingest",
        "--labels", str(queries_tiny_path),
        "--traces", str(traces_rag_path), str(traces_tua_path),
        "--out", str(env_path),
    ])
    capsys.readouterr()

    scored_path = tmp_path / "scored.jsonl"
    main([
        "score",
        "--rubric", "refusal",
        "--ingested", str(env_path),
        "--out", str(scored_path),
    ])
    capsys.readouterr()

    rc = main(["report", "--scored", str(scored_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "# Eval report" in captured.out


def test_main_ingest_requires_labels():
    with pytest.raises(SystemExit):
        main(["ingest"])


def test_main_score_requires_rubric_and_ingested():
    with pytest.raises(SystemExit):
        main(["score"])


def test_main_report_requires_scored():
    with pytest.raises(SystemExit):
        main(["report"])


def test_main_score_rejects_unknown_rubric():
    """argparse choices= enforces the rubric vocabulary at parse time."""
    with pytest.raises(SystemExit):
        main(["score", "--rubric", "nonsense", "--ingested", "/tmp/none"])
