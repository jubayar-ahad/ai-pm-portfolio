#!/usr/bin/env bash
# make-demo.sh — one-shot rag-app demo across all three corpora.
#
# Loads cursor-docs/ + anthropic-docs/ + willison/ into a single
# .cache/demo-chunks.jsonl, then runs `python -m rag_app ask --dry-run` on a
# hand-picked cross-corpus question (one that needs all three sub-corpora to
# answer well). Dry-run means no ANTHROPIC_API_KEY is required; the script
# is safe to run in CI or a sandbox. The printed retrieved-chunks block and
# the constructed prompt are suitable for pasting into rag-app/README.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer `python` on the PATH (the README's convention), fall back to
# `python3` (Homebrew / system Python on macOS where `python` is unaliased).
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "make-demo.sh: neither python nor python3 found on PATH" >&2
    exit 1
fi

CHUNKS_REL="rag-app/.cache/demo-chunks.jsonl"
DEMO_QUESTION="What are agent skills, and how do Cursor and Anthropic implement them?"

mkdir -p .cache

echo ">>> Loading cursor-docs/ + anthropic-docs/ + willison/ into ${CHUNKS_REL}"
"${PY}" - <<'PY'
from pathlib import Path

from rag_app.corpus import find_repo_root, load_and_chunk, write_chunks

repo_root = find_repo_root(Path.cwd())
corpus_dir = repo_root / "rag-app" / "corpus"
subdirs = ("cursor-docs", "anthropic-docs", "willison")
files = tuple(sorted(
    str(p.relative_to(repo_root))
    for sub in subdirs
    for p in (corpus_dir / sub).glob("*.md")
))
chunks = load_and_chunk(repo_root, files=files)
out_path = repo_root / "rag-app" / ".cache" / "demo-chunks.jsonl"
write_chunks(chunks, out_path)

per_sub = {sub: 0 for sub in subdirs}
for chunk in chunks:
    head = chunk.source.split("/", 3)[2]  # rag-app/corpus/<sub>/<file>
    if head in per_sub:
        per_sub[head] += 1

print(f"Wrote {len(chunks)} chunks from {len(files)} files to {out_path.relative_to(repo_root)}")
for sub in subdirs:
    print(f"  {sub}: {per_sub[sub]} chunks")
PY

echo ""
echo ">>> Cross-corpus demo question:"
echo "    ${DEMO_QUESTION}"
echo ""
echo ">>> python -m rag_app ask --dry-run --chunks ${CHUNKS_REL} --top-k 5 \"<question>\""
echo ""

"${PY}" -m rag_app ask \
    --dry-run \
    --chunks "${CHUNKS_REL}" \
    --top-k 5 \
    "${DEMO_QUESTION}"
