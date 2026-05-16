"""Command-line entry point for the rag-app demo.

Subcommands land iteratively. As of this iteration: `load`, `retrieve`, `ask`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from rag_app.corpus import (
    DEFAULT_CHUNK_WORDS,
    DEFAULT_CORPUS_FILES,
    DEFAULT_OVERLAP_WORDS,
    find_repo_root,
    load_and_chunk,
    write_chunks,
)
from rag_app.generate import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    build_prompt,
    call_claude,
)
from rag_app.retrieve import (
    DEFAULT_TOP_K,
    BM25Index,
    load_chunks,
)

DEFAULT_CHUNKS_PATH = "rag-app/.cache/chunks.jsonl"


def _resolve(path_arg: str, repo_root: Path) -> Path:
    p = Path(path_arg)
    return p if p.is_absolute() else (repo_root / p)


def cmd_load(args: argparse.Namespace) -> int:
    if args.corpus_root:
        corpus_root = Path(args.corpus_root).resolve()
    else:
        corpus_root = find_repo_root(Path(__file__).resolve().parent)

    out_path = _resolve(args.out, corpus_root)

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


def cmd_retrieve(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path(__file__).resolve().parent)
    chunks_path = _resolve(args.chunks, repo_root)
    indexed = load_chunks(chunks_path)
    index = BM25Index(indexed)
    results = index.query(args.question, top_k=args.top_k)

    if args.json:
        payload = {
            "question": args.question,
            "top_k": args.top_k,
            "results": [
                {
                    "rank": r.rank,
                    "score": round(r.score, 6),
                    "id": r.id,
                    "source": r.source,
                    "span": list(r.span),
                    "text": r.text,
                }
                for r in results
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print(f"No chunks matched query: {args.question!r}")
        return 0

    print(f"Question: {args.question}")
    print(f"Top {len(results)} of {len(indexed)} chunks (BM25):")
    print()
    for r in results:
        preview = r.text.replace("\n", " ")
        if len(preview) > 200:
            preview = preview[:197] + "..."
        print(f"  #{r.rank}  score={r.score:6.3f}  {r.id}  span={r.span}")
        print(f"        {preview}")
        print()
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path(__file__).resolve().parent)
    chunks_path = _resolve(args.chunks, repo_root)
    indexed = load_chunks(chunks_path)
    index = BM25Index(indexed)
    retrieved = index.query(args.question, top_k=args.top_k)
    prompt = build_prompt(args.question, retrieved)

    have_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    do_live = not args.dry_run and have_key
    mode = "live" if do_live else "dry-run"

    answer = call_claude(prompt, model=args.model, max_tokens=args.max_tokens) if do_live else None

    if args.json:
        payload = {
            "mode": mode,
            "question": args.question,
            "top_k": args.top_k,
            "retrieved": [
                {
                    "rank": r.rank,
                    "score": round(r.score, 6),
                    "id": r.id,
                    "source": r.source,
                    "span": list(r.span),
                    "text": r.text,
                }
                for r in retrieved
            ],
            "prompt": {"system": prompt.system, "user": prompt.user},
            "answer": asdict(answer) if answer is not None else None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Question: {args.question}")
    print(f"Mode: {mode}")
    if not do_live and not args.dry_run and not have_key:
        print("  (no ANTHROPIC_API_KEY in environment — falling back to dry-run)")
    print(f"Retrieved {len(retrieved)} of {len(indexed)} chunks:")
    for r in retrieved:
        print(f"  #{r.rank}  score={r.score:6.3f}  {r.id}  span={r.span}")
    print()

    if answer is None:
        print("--- prompt.system ---")
        print(prompt.system)
        print("--- prompt.user ---")
        print(prompt.user)
        print()
        print("(dry-run: no model call made)")
        return 0

    print("--- answer ---")
    print(answer.text)
    print()
    print(
        f"(model={answer.model}  "
        f"input_tokens={answer.input_tokens}  "
        f"output_tokens={answer.output_tokens})"
    )
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
        default=DEFAULT_CHUNKS_PATH,
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

    p_retrieve = sub.add_parser(
        "retrieve",
        help="Rank chunks against a question using BM25",
    )
    p_retrieve.add_argument(
        "question",
        help="Natural-language question to retrieve against.",
    )
    p_retrieve.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"How many chunks to return (default {DEFAULT_TOP_K}).",
    )
    p_retrieve.add_argument(
        "--chunks",
        default=DEFAULT_CHUNKS_PATH,
        help="Path to chunks.jsonl (relative to repo root unless absolute).",
    )
    p_retrieve.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON object instead of a human-readable summary.",
    )
    p_retrieve.set_defaults(func=cmd_retrieve)

    p_ask = sub.add_parser(
        "ask",
        help="Retrieve top-k chunks and ask Claude to answer with citations",
    )
    p_ask.add_argument(
        "question",
        help="Natural-language question to answer.",
    )
    p_ask.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"How many chunks to feed the model (default {DEFAULT_TOP_K}).",
    )
    p_ask.add_argument(
        "--chunks",
        default=DEFAULT_CHUNKS_PATH,
        help="Path to chunks.jsonl (relative to repo root unless absolute).",
    )
    p_ask.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Anthropic model id (default {DEFAULT_MODEL}).",
    )
    p_ask.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Max output tokens (default {DEFAULT_MAX_TOKENS}).",
    )
    p_ask.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and print the prompt without calling Claude. Auto-enabled if ANTHROPIC_API_KEY is unset.",
    )
    p_ask.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON record (question, retrieved, prompt, answer) for the evals harness.",
    )
    p_ask.set_defaults(func=cmd_ask)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
