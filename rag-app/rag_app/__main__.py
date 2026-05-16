"""Command-line entry point for the rag-app demo.

Subcommands land iteratively. As of this iteration: `load` only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rag_app.corpus import (
    DEFAULT_CHUNK_WORDS,
    DEFAULT_CORPUS_FILES,
    DEFAULT_OVERLAP_WORDS,
    find_repo_root,
    load_and_chunk,
    write_chunks,
)


def cmd_load(args: argparse.Namespace) -> int:
    if args.corpus_root:
        corpus_root = Path(args.corpus_root).resolve()
    else:
        corpus_root = find_repo_root(Path(__file__).resolve().parent)

    out_arg = Path(args.out)
    out_path = out_arg if out_arg.is_absolute() else (corpus_root / out_arg)

    chunks = load_and_chunk(
        corpus_root=corpus_root,
        chunk_words=args.chunk_words,
        overlap_words=args.overlap_words,
    )
    write_chunks(chunks, out_path)

    counts: dict[str, int] = {}
    for chunk in chunks:
        counts[chunk.source] = counts.get(chunk.source, 0) + 1
    print(f"Wrote {len(chunks)} chunks to {out_path}")
    for source in DEFAULT_CORPUS_FILES:
        print(f"  {source}: {counts.get(source, 0)} chunks")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rag_app")
    sub = parser.add_subparsers(dest="command", required=True)

    p_load = sub.add_parser(
        "load",
        help="Load corpus markdown files and write chunks.jsonl",
    )
    p_load.add_argument(
        "--corpus-root",
        default=None,
        help="Repo root containing the corpus files. Default: auto-detect by walking up from the package location until OBJECTIVE.md is found.",
    )
    p_load.add_argument(
        "--out",
        default="rag-app/.cache/chunks.jsonl",
        help="Output JSONL path (relative to corpus root unless absolute).",
    )
    p_load.add_argument(
        "--chunk-words",
        type=int,
        default=DEFAULT_CHUNK_WORDS,
        help=f"Target words per chunk (default {DEFAULT_CHUNK_WORDS}).",
    )
    p_load.add_argument(
        "--overlap-words",
        type=int,
        default=DEFAULT_OVERLAP_WORDS,
        help=f"Paragraph-level overlap budget in words (default {DEFAULT_OVERLAP_WORDS}).",
    )
    p_load.set_defaults(func=cmd_load)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
