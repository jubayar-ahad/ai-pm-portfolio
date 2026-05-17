"""Tests for the rag_app.__main__ CLI dispatch.

Exercises cmd_load, cmd_retrieve, and the main() argparse surface so the
package's CLI plumbing is exercised alongside the library-level tests.
No live model calls; the `ask` live path is intentionally out of scope.
"""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from rag_app.__main__ import (
    DEFAULT_CHUNKS_PATH,
    cmd_load,
    cmd_retrieve,
    main,
)
from rag_app.corpus import (
    DEFAULT_CHUNK_WORDS,
    DEFAULT_CORPUS_FILES,
    DEFAULT_OVERLAP_WORDS,
    load_and_chunk,
    write_chunks,
)
from rag_app.retrieve import DEFAULT_TOP_K

TINY_CORPUS_FILES: tuple[str, ...] = ("animals.md", "sub/cities.md")


def _capture(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*args, **kwargs)
    assert rc == 0
    return buf.getvalue()


def _materialize_chunks(tiny_corpus_root: Path, tmp_path: Path) -> Path:
    chunks = load_and_chunk(corpus_root=tiny_corpus_root, files=TINY_CORPUS_FILES)
    out = tmp_path / "chunks.jsonl"
    write_chunks(chunks, out)
    return out


def test_cmd_load_writes_chunks_jsonl(tiny_corpus_root: Path, tmp_path: Path):
    """cmd_load with an explicit --corpus-root must produce chunks.jsonl
    against that root, even when the corpus file list is the default."""
    # Stage tiny corpus copies under the names DEFAULT_CORPUS_FILES expects so
    # cmd_load's defaults resolve. We're testing CLI dispatch shape, not the
    # corpus contents.
    staged = tmp_path / "staged_corpus"
    staged.mkdir()
    (staged / "OBJECTIVE.md").write_text("# Stub objective\n", encoding="utf-8")
    (staged / "DECISIONS.md").write_text("# Stub decisions\n\nA paragraph.\n", encoding="utf-8")
    (staged / "templates").mkdir()
    (staged / "templates" / "INTERVIEW_TRACKER.md").write_text(
        "# Stub tracker\n\nAnother paragraph.\n", encoding="utf-8"
    )
    (staged / "rag-app").mkdir()
    (staged / "rag-app" / "README.md").write_text(
        "# Stub rag-app README\n\nMore prose.\n", encoding="utf-8"
    )

    out_path = tmp_path / "chunks.jsonl"
    args = argparse.Namespace(
        command="load",
        corpus_root=str(staged),
        out=str(out_path),
        chunk_words=DEFAULT_CHUNK_WORDS,
        overlap_words=DEFAULT_OVERLAP_WORDS,
    )
    stdout = _capture(cmd_load, args)
    assert out_path.is_file()
    assert "Wrote" in stdout
    # Per-source line printed for each DEFAULT_CORPUS_FILES entry
    for source in DEFAULT_CORPUS_FILES:
        assert source in stdout
    # Validate JSONL shape
    lines = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    assert len(lines) >= 4
    for rec in lines:
        assert set(rec.keys()) == {"id", "source", "span", "word_count", "text"}


def test_cmd_retrieve_human_output(tiny_corpus_root: Path, tmp_path: Path, monkeypatch):
    chunks_path = _materialize_chunks(tiny_corpus_root, tmp_path)
    # Anchor find_repo_root to the tmp_path tree via cwd, but cmd_retrieve
    # uses chunks resolved relative to repo_root only when the path is
    # relative — we pass an absolute path so the resolve step is a no-op.
    args = argparse.Namespace(
        command="retrieve",
        question="Pangolins",
        top_k=DEFAULT_TOP_K,
        chunks=str(chunks_path),
        json=False,
    )
    stdout = _capture(cmd_retrieve, args)
    assert "Question: Pangolins" in stdout
    assert "Top " in stdout
    assert "score=" in stdout


def test_cmd_retrieve_json_output(tiny_corpus_root: Path, tmp_path: Path):
    chunks_path = _materialize_chunks(tiny_corpus_root, tmp_path)
    args = argparse.Namespace(
        command="retrieve",
        question="Reykjavik",
        top_k=3,
        chunks=str(chunks_path),
        json=True,
    )
    stdout = _capture(cmd_retrieve, args)
    payload = json.loads(stdout)
    assert payload["question"] == "Reykjavik"
    assert payload["top_k"] == 3
    assert isinstance(payload["results"], list)
    assert payload["results"][0]["source"] == "sub/cities.md"
    # span is serialized as a JSON list of two ints
    span = payload["results"][0]["span"]
    assert isinstance(span, list) and len(span) == 2


def test_cmd_retrieve_no_matches(tiny_corpus_root: Path, tmp_path: Path):
    chunks_path = _materialize_chunks(tiny_corpus_root, tmp_path)
    args = argparse.Namespace(
        command="retrieve",
        question="quasar nucleosynthesis nowhere",
        top_k=DEFAULT_TOP_K,
        chunks=str(chunks_path),
        json=False,
    )
    stdout = _capture(cmd_retrieve, args)
    assert "No chunks matched" in stdout


def test_main_no_args_errors(capsys):
    # argparse exits with SystemExit(2) when a required subcommand is missing.
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_main_help_exits_clean(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "load" in captured.out
    assert "retrieve" in captured.out
    assert "ask" in captured.out


def test_main_dispatches_to_retrieve(tiny_corpus_root: Path, tmp_path: Path, capsys):
    """End-to-end via main(): argparse → cmd_retrieve → JSON stdout."""
    chunks_path = _materialize_chunks(tiny_corpus_root, tmp_path)
    rc = main(
        [
            "retrieve",
            "axolotl",
            "--top-k",
            "1",
            "--chunks",
            str(chunks_path),
            "--json",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["question"] == "axolotl"
    assert payload["top_k"] == 1
    assert payload["results"][0]["source"] == "animals.md"
