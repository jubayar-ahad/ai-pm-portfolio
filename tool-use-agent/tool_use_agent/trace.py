"""Eval-harness-ready trace metadata for the `ask` slice.

Mirrors ``rag-app/rag_app/trace.py`` structurally — same hashing algorithm
(canonical JSON with sorted keys → SHA-256 → 16-hex-char truncation),
same timestamp shape — so the future ``evals-harness/`` build can use
one verification path across both builds. The two trace modules
deliberately do *not* cross-import: each top-level build remains
self-contained, and the cross-build alignment is a startup assertion
the harness will own.

The four trace fields a record carries:

- ``schema_version`` — constant ``"tool-use-agent.ask.v1"``. The
  rag-app build carries ``"rag-app.ask.v1"``; the harness routes on
  prefix. Additive top-level fields keep the version; renames or
  removed fields require a bump.
- ``corpus_fingerprint`` — SHA-256 of the canonical-JSON serialization
  of ``catalog_as_anthropic_tools()`` (the surface the model actually
  sees), truncated to 16 hex chars. The tool-use agent has no chunks
  file; its analog of a corpus is the catalog. Adding, removing, or
  re-describing a tool changes the fingerprint; refactoring an
  ``impl`` function without changing its surface does not. The JSON
  field name stays ``corpus_fingerprint`` so the harness can pivot on
  one key across both builds.
- ``record_id`` — SHA-256 over the canonical JSON of the *logical
  query* tuple ``{schema, question, model, max_steps, mode,
  corpus_fingerprint}``, truncated to 16 hex chars. The same logical
  query against the same catalog produces the same id on different
  days. ``generated_at`` is excluded on purpose for that reason.
- ``generated_at`` — ISO-8601 UTC with second precision and a ``Z``
  suffix. Lets the harness sort chronologically without parsing
  filenames.

All four are deterministic given their inputs — no env-dependent
values, no randomness — so replaying the same inputs produces the
same record_id/corpus_fingerprint, which is the property the harness
needs to compare cross-run records.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "tool-use-agent.ask.v1"

# Match rag-app's truncation: 16 hex chars = 64 bits, plenty to
# disambiguate within a single eval run while staying skim-friendly in
# diffs.
_HEX_LEN = 16


def catalog_canonical_bytes(catalog: list[dict[str, Any]]) -> bytes:
    """Stable, byte-for-byte serialization of the model-facing catalog.

    Sorted keys so dict iteration order does not perturb the digest.
    ``ensure_ascii=False`` keeps unicode characters in the description
    literal rather than escaping them, matching how the SDK serializes
    them for the model.
    """
    return json.dumps(catalog, sort_keys=True, ensure_ascii=False).encode(
        "utf-8"
    )


def compute_corpus_fingerprint(catalog: list[dict[str, Any]]) -> str:
    """SHA-256 of the canonical catalog bytes, truncated to 16 hex chars."""
    return hashlib.sha256(catalog_canonical_bytes(catalog)).hexdigest()[
        :_HEX_LEN
    ]


def compute_record_id(
    *,
    question: str,
    model: str,
    max_steps: int,
    mode: str,
    corpus_fingerprint: str,
) -> str:
    """Deterministic short hex id for a logical ask-query."""
    payload = json.dumps(
        {
            "schema": SCHEMA_VERSION,
            "question": question,
            "model": model,
            "max_steps": max_steps,
            "mode": mode,
            "corpus_fingerprint": corpus_fingerprint,
        },
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:_HEX_LEN]


def now_iso() -> str:
    """ISO-8601 UTC timestamp with second precision, no microseconds."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
