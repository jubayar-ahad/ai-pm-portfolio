"""Read-and-validate pass over labeled queries + trace records.

Implements ``python -m evals_harness ingest``. The contract:

- Read ``--labels`` JSONL. Validate every record has exactly the 9-key
  shape locked in DECISIONS (iteration 16) and that each enum-valued
  field is in its locked vocabulary.
- Read each ``--traces`` JSONL file. Validate every record carries a
  ``schema_version`` in the known-version list and the three
  cross-cuttable fields the scorer rubrics will need
  (``record_id``, ``corpus_fingerprint``, ``question``).
- Run the two startup invariants from ``invariants.py``. Fail-fast on
  any drift with a named error.
- Optionally emit a normalized ``ingested.jsonl`` with one record per
  input line, wrapped in a ``{"kind": "label"|"trace", ...}`` envelope
  so the slice-3 scorer can route without re-parsing each record.

The harness rejects unknown schema versions rather than silently
downgrading them. The 9-key label schema is enforced exactly: missing
or extra keys raise. Both invariants must pass before any record is
written; partial-output failure modes are explicitly avoided.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .invariants import InvariantError, run_startup_invariants

KNOWN_SCHEMAS: frozenset[str] = frozenset(
    {"rag-app.ask.v1", "tool-use-agent.ask.v1"}
)

LABEL_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "question",
        "shape",
        "expected_outcome",
        "applies_to",
        "expected_citation_source",
        "expected_first_tool",
        "corpus_fingerprint_at_label",
        "notes",
    }
)

SHAPE_VOCAB: frozenset[str] = frozenset(
    {"in_corpus", "out_of_corpus", "tracker_rollup", "adversarial_in_corpus"}
)

OUTCOME_VOCAB: frozenset[str] = frozenset({"answer", "refuse"})

# Trace-record fields the slice-3+ rubrics will rely on. Other per-build
# fields (e.g. rag-app's ``verification``, tool-use-agent's
# ``refusal_reason``) are not required at ingest because each scorer
# routes by schema_version and validates its own per-build fields.
REQUIRED_TRACE_FIELDS: tuple[str, ...] = (
    "schema_version",
    "record_id",
    "corpus_fingerprint",
    "question",
)


class IngestError(RuntimeError):
    """Raised when an input record fails schema validation."""


@dataclass(frozen=True)
class IngestResult:
    labels: list[dict[str, Any]]
    traces: list[dict[str, Any]]
    invariants: list[Any]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fp:
        for lineno, raw in enumerate(fp, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise IngestError(
                    f"{path}:{lineno}: invalid JSON ({exc.msg})"
                ) from exc
            if not isinstance(rec, dict):
                raise IngestError(
                    f"{path}:{lineno}: record must be a JSON object, got "
                    f"{type(rec).__name__}"
                )
            records.append(rec)
    return records


def validate_label(rec: dict[str, Any], path: Path, lineno: int) -> None:
    keys = set(rec.keys())
    if keys != LABEL_KEYS:
        missing = sorted(LABEL_KEYS - keys)
        extra = sorted(keys - LABEL_KEYS)
        raise IngestError(
            f"{path}:{lineno}: label key set mismatch "
            f"(missing={missing}, extra={extra})"
        )

    shape = rec["shape"]
    if shape not in SHAPE_VOCAB:
        raise IngestError(
            f"{path}:{lineno}: shape={shape!r} not in "
            f"{sorted(SHAPE_VOCAB)}"
        )

    outcome = rec["expected_outcome"]
    if outcome not in OUTCOME_VOCAB:
        raise IngestError(
            f"{path}:{lineno}: expected_outcome={outcome!r} not in "
            f"{sorted(OUTCOME_VOCAB)}"
        )

    applies_to = rec["applies_to"]
    if not isinstance(applies_to, list) or not applies_to:
        raise IngestError(
            f"{path}:{lineno}: applies_to must be a non-empty list, "
            f"got {applies_to!r}"
        )
    unknown = [s for s in applies_to if s not in KNOWN_SCHEMAS]
    if unknown:
        raise IngestError(
            f"{path}:{lineno}: applies_to contains unknown schema(s) "
            f"{unknown}; known: {sorted(KNOWN_SCHEMAS)}"
        )

    fingerprints = rec["corpus_fingerprint_at_label"]
    if not isinstance(fingerprints, dict):
        raise IngestError(
            f"{path}:{lineno}: corpus_fingerprint_at_label must be a "
            f"dict, got {type(fingerprints).__name__}"
        )
    if set(fingerprints.keys()) != set(applies_to):
        raise IngestError(
            f"{path}:{lineno}: corpus_fingerprint_at_label keys "
            f"{sorted(fingerprints)} != applies_to {sorted(applies_to)}"
        )


def validate_trace(rec: dict[str, Any], path: Path, lineno: int) -> None:
    missing = [f for f in REQUIRED_TRACE_FIELDS if f not in rec]
    if missing:
        raise IngestError(
            f"{path}:{lineno}: trace record missing required field(s) "
            f"{missing}"
        )
    schema = rec["schema_version"]
    if schema not in KNOWN_SCHEMAS:
        raise IngestError(
            f"{path}:{lineno}: schema_version={schema!r} not in known "
            f"versions {sorted(KNOWN_SCHEMAS)}"
        )


def ingest(
    label_path: Path,
    trace_paths: list[Path],
) -> IngestResult:
    """Run invariants, validate inputs, return parsed records.

    Invariants run first so a label/trace schema bug does not mask a
    cross-build drift that would otherwise produce a silently-wrong
    report.
    """
    invariants = run_startup_invariants()

    labels = _read_jsonl(label_path)
    for lineno, rec in enumerate(labels, start=1):
        validate_label(rec, label_path, lineno)

    traces: list[dict[str, Any]] = []
    for tpath in trace_paths:
        recs = _read_jsonl(tpath)
        for lineno, rec in enumerate(recs, start=1):
            validate_trace(rec, tpath, lineno)
        traces.extend(recs)

    return IngestResult(labels=labels, traces=traces, invariants=invariants)


def _write_normalized(
    out_path: Path,
    result: IngestResult,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        for rec in result.labels:
            fp.write(
                json.dumps(
                    {
                        "kind": "label",
                        "id": rec["id"],
                        "applies_to": rec["applies_to"],
                        "record": rec,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        for rec in result.traces:
            fp.write(
                json.dumps(
                    {
                        "kind": "trace",
                        "schema_version": rec["schema_version"],
                        "record_id": rec["record_id"],
                        "record": rec,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def cmd_ingest(args: argparse.Namespace) -> int:
    label_path = Path(args.labels)
    trace_paths = [Path(p) for p in (args.traces or [])]

    try:
        result = ingest(label_path, trace_paths)
    except InvariantError as exc:
        print(f"INVARIANT FAILED: {exc}", file=sys.stderr)
        return 2
    except IngestError as exc:
        print(f"INGEST FAILED: {exc}", file=sys.stderr)
        return 2

    if args.out:
        _write_normalized(Path(args.out), result)

    print(
        f"{len(result.traces)} traces, {len(result.labels)} labels, "
        f"{len(result.invariants)} invariant checks passed"
    )
    if args.verbose:
        for inv in result.invariants:
            print(f"  ok: {inv.name} ({inv.detail})")
    return 0
