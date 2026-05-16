"""Eval-harness-ready trace metadata for the `ask` slice.

The future ``evals-harness/`` build replays ``ask --json`` records and
scores them. Four small fields make those records diff-able across runs
without the harness having to reverse-engineer identity from filenames
or hash the prompt by hand:

- ``schema_version`` — constant string so the harness can version-gate.
  Bumping it is a deliberate breaking-change signal; additive fields
  keep the same version.
- ``corpus_fingerprint`` — short hex of ``chunks.jsonl`` bytes. Lets
  the harness detect that the underlying corpus changed between two
  records that otherwise look identical, which would otherwise silently
  invalidate a comparison.
- ``record_id`` — deterministic short hex over the *logical query* tuple
  (question, top_k, model, min_score, corpus_fingerprint, mode). The
  same logical query against the same corpus produces the same id; any
  change in any of those inputs produces a new id. Excludes
  ``generated_at`` on purpose, since wall-clock time is not part of the
  query.
- ``generated_at`` — ISO-8601 UTC timestamp so the harness can sort
  records chronologically without parsing filenames.

All four fields are mechanical and deterministic given their inputs.
No env-dependent values, no randomness — replaying the same inputs
produces the same record_id and corpus_fingerprint, which is the
property the harness needs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "rag-app.ask.v1"

# 16 hex chars = 64 bits, plenty to disambiguate within a single eval
# run while staying skim-friendly in human output and diffs.
_HEX_LEN = 16


def compute_corpus_fingerprint(chunks_path: Path) -> str:
    """SHA-256 of the chunks.jsonl bytes, truncated to 16 hex chars.

    Faithful to "what was actually loaded": if the loader produced a
    different chunks.jsonl (different chunker params, corpus edits,
    file order), the fingerprint changes. Deterministic given a fixed
    on-disk file.
    """
    h = hashlib.sha256()
    with open(chunks_path, "rb") as fp:
        for block in iter(lambda: fp.read(65536), b""):
            h.update(block)
    return h.hexdigest()[:_HEX_LEN]


def compute_record_id(
    *,
    question: str,
    top_k: int,
    model: str,
    min_score: float,
    corpus_fingerprint: str,
    mode: str,
) -> str:
    """Deterministic short hex id for a logical ask-query.

    Two records with the same id describe the same logical query
    executed against the same corpus, even if they ran on different
    days. The harness uses this to group records for cross-run
    comparison.
    """
    payload = json.dumps(
        {
            "schema": SCHEMA_VERSION,
            "question": question,
            "top_k": top_k,
            "model": model,
            "min_score": min_score,
            "corpus_fingerprint": corpus_fingerprint,
            "mode": mode,
        },
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:_HEX_LEN]


def now_iso() -> str:
    """ISO-8601 UTC timestamp with second precision, no microseconds.

    Second precision is enough for ordering across runs and keeps the
    record visually clean. ``Z`` suffix marks UTC unambiguously.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
