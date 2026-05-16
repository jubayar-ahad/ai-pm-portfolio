"""Refusal-bucket scorer (slice 3) for the evals harness.

Reads a normalized ``ingested.jsonl`` envelope produced by ``ingest``,
joins traces to labels by (question, schema_version ∈ applies_to),
classifies each trace's observed outcome as ``refuse`` / ``answer`` /
``no_observation``, and emits a per-record scored JSONL plus a small
per-build Markdown confusion matrix on stdout.

The classifier is build-specific because the two builds expose their
refusal signal differently:

* rag-app emits ``mode == "refused-low-score"`` for the threshold-bypass
  path (no model call) and otherwise carries the model's answer in
  ``answer.text``. A model-emitted refusal is detected by strict-strip
  byte-equality with ``REFUSAL_SENTENCE``.
* tool-use-agent always carries the final string in ``final_text``;
  ``refusal_reason`` is set to one of ``model_refused`` /
  ``repeated_tool_error`` / ``max_steps_exhausted`` whenever the canonical
  refusal is emitted. Both signals are checked and required to agree
  (a divergence would surface as ``RuntimeError`` because it indicates
  a build bug the slice-2 invariants did not catch).
* Dry-run traces carry no answer / no final_text. They are classified as
  ``no_observation`` so they do not pollute the confusion matrix; the
  Markdown report counts them separately as a diagnostic row.

Cross-build alignment: ``REFUSAL_SENTENCE`` is imported from
``rag_app.verify`` because the slice-2 startup invariant has already
asserted byte-equality with ``tool_use_agent.verify.REFUSAL_SENTENCE``.
The score command re-runs the invariants before doing any work so a
drift introduced between an ``ingest`` run and a ``score`` run is still
caught.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import _repo
from .invariants import InvariantError, run_startup_invariants

RUBRIC = "refusal"

OBSERVED_REFUSE = "refuse"
OBSERVED_ANSWER = "answer"
OBSERVED_NONE = "no_observation"


class ScoreError(RuntimeError):
    """Raised on malformed envelope input or on cross-build inconsistency
    the scorer catches at run time."""


@dataclass(frozen=True)
class ScoredRow:
    rubric: str
    record_id: str
    schema_version: str
    question: str
    label_id: str
    expected_outcome: str
    observed_outcome: str
    mode: str
    match: bool


@dataclass
class ScoreResult:
    rows: list[ScoredRow] = field(default_factory=list)
    # Counts of envelopes seen and how they paired:
    n_labels: int = 0
    n_traces: int = 0
    n_unpaired_traces: int = 0  # traces with no label matching question+schema
    n_unpaired_labels: int = 0  # labels with no trace at all


def _read_envelope(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split the ingested envelope into label-records and trace-records.

    Each envelope line is ``{"kind": "label"|"trace", ..., "record": {...}}``;
    we hand back the original ``record`` body so per-build classifiers can
    read the fields they need without unpacking an envelope shape.
    """
    labels: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fp:
        for lineno, raw in enumerate(fp, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                env = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ScoreError(
                    f"{path}:{lineno}: invalid JSON ({exc.msg})"
                ) from exc
            if not isinstance(env, dict) or "kind" not in env or "record" not in env:
                raise ScoreError(
                    f"{path}:{lineno}: envelope must have keys "
                    f"'kind' and 'record'; got keys={sorted(env)}"
                )
            kind = env["kind"]
            record = env["record"]
            if kind == "label":
                labels.append(record)
            elif kind == "trace":
                traces.append(record)
            else:
                raise ScoreError(
                    f"{path}:{lineno}: unknown envelope kind {kind!r}; "
                    f"expected 'label' or 'trace'"
                )
    return labels, traces


def classify_rag_app(trace: dict[str, Any]) -> str:
    """Observed outcome for a ``rag-app.ask.v1`` trace."""
    # Lazy import: invariants have already prepended rag-app/ to sys.path.
    from rag_app.verify import REFUSAL_SENTENCE

    mode = trace.get("mode")
    if mode == "refused-low-score":
        return OBSERVED_REFUSE
    if mode != "live":
        return OBSERVED_NONE
    answer = trace.get("answer")
    if not isinstance(answer, dict):
        return OBSERVED_NONE
    text = answer.get("text")
    if not isinstance(text, str):
        return OBSERVED_NONE
    if text.strip() == REFUSAL_SENTENCE:
        return OBSERVED_REFUSE
    return OBSERVED_ANSWER


def classify_tool_use_agent(trace: dict[str, Any]) -> str:
    """Observed outcome for a ``tool-use-agent.ask.v1`` trace.

    Cross-checks ``refusal_reason`` against ``final_text == REFUSAL_SENTENCE``;
    a mismatch raises ``ScoreError`` because it indicates a build bug the
    slice-2 invariants did not anticipate.
    """
    from tool_use_agent.verify import REFUSAL_SENTENCE

    mode = trace.get("mode")
    if mode != "live":
        return OBSERVED_NONE
    final_text = trace.get("final_text")
    refusal_reason = trace.get("refusal_reason")
    if not isinstance(final_text, str) or not final_text:
        return OBSERVED_NONE
    is_refusal_by_text = final_text.strip() == REFUSAL_SENTENCE
    is_refusal_by_reason = refusal_reason is not None
    if is_refusal_by_text != is_refusal_by_reason:
        rid = trace.get("record_id", "?")
        raise ScoreError(
            f"tool-use-agent trace {rid}: final_text-vs-refusal_reason "
            f"disagree (text-equals-refusal={is_refusal_by_text}, "
            f"refusal_reason={refusal_reason!r}); build bug suspected"
        )
    return OBSERVED_REFUSE if is_refusal_by_text else OBSERVED_ANSWER


_CLASSIFIERS = {
    "rag-app.ask.v1": classify_rag_app,
    "tool-use-agent.ask.v1": classify_tool_use_agent,
}


def classify(trace: dict[str, Any]) -> str:
    schema = trace.get("schema_version")
    classifier = _CLASSIFIERS.get(schema)
    if classifier is None:
        raise ScoreError(
            f"unknown schema_version {schema!r}; cannot classify trace "
            f"{trace.get('record_id')!r}"
        )
    return classifier(trace)


def _index_labels_by_question(
    labels: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Map ``question`` -> list of labels carrying that question.

    Duplicates are not expected in queries.jsonl (slice 1's hand-author
    contract) but the scorer accepts them without merging — each label is
    a separate row in the envelope and stays independently joinable.
    """
    by_q: dict[str, list[dict[str, Any]]] = {}
    for rec in labels:
        by_q.setdefault(rec["question"], []).append(rec)
    return by_q


def score_refusal(envelope_path: Path) -> ScoreResult:
    """Run the refusal rubric over a normalized ingested.jsonl envelope.

    Joins each trace to a label by (trace.question, schema_version ∈
    label.applies_to). Emits one ScoredRow per matched (label, trace)
    pair, plus diagnostic counts of unpaired records on either side.
    """
    labels, traces = _read_envelope(envelope_path)
    labels_by_q = _index_labels_by_question(labels)

    rows: list[ScoredRow] = []
    matched_label_ids: set[str] = set()
    unpaired_traces = 0

    for trace in traces:
        question = trace.get("question")
        schema = trace.get("schema_version")
        candidates = [
            lab
            for lab in labels_by_q.get(question, [])
            if schema in lab.get("applies_to", [])
        ]
        if not candidates:
            unpaired_traces += 1
            continue

        observed = classify(trace)
        for lab in candidates:
            expected = lab["expected_outcome"]
            match = (observed == expected) if observed != OBSERVED_NONE else False
            rows.append(
                ScoredRow(
                    rubric=RUBRIC,
                    record_id=trace["record_id"],
                    schema_version=schema,
                    question=question,
                    label_id=lab["id"],
                    expected_outcome=expected,
                    observed_outcome=observed,
                    mode=trace.get("mode", ""),
                    match=match,
                )
            )
            matched_label_ids.add(lab["id"])

    unpaired_labels = sum(
        1 for lab in labels if lab["id"] not in matched_label_ids
    )

    rows.sort(key=lambda r: (r.schema_version, r.record_id, r.label_id))

    return ScoreResult(
        rows=rows,
        n_labels=len(labels),
        n_traces=len(traces),
        n_unpaired_traces=unpaired_traces,
        n_unpaired_labels=unpaired_labels,
    )


def _confusion_counts(
    rows: list[ScoredRow], schema: str
) -> dict[tuple[str, str], int]:
    """(expected, observed) -> count for one build."""
    out: dict[tuple[str, str], int] = {}
    for r in rows:
        if r.schema_version != schema:
            continue
        key = (r.expected_outcome, r.observed_outcome)
        out[key] = out.get(key, 0) + 1
    return out


_EXPECTED = (OBSERVED_REFUSE, OBSERVED_ANSWER)
_OBSERVED = (OBSERVED_REFUSE, OBSERVED_ANSWER, OBSERVED_NONE)


def render_refusal_report(result: ScoreResult) -> str:
    """Render a per-build refusal confusion matrix as Markdown."""
    schemas_seen = sorted({r.schema_version for r in result.rows})
    lines: list[str] = []
    lines.append("# Refusal rubric")
    lines.append("")
    lines.append(
        f"labels={result.n_labels}  traces={result.n_traces}  "
        f"scored_rows={len(result.rows)}  "
        f"unpaired_traces={result.n_unpaired_traces}  "
        f"unpaired_labels={result.n_unpaired_labels}"
    )
    lines.append("")

    if not schemas_seen:
        lines.append("(no paired (label, trace) records — nothing to score)")
        return "\n".join(lines) + "\n"

    lines.append(
        "| build | expected | observed=refuse | observed=answer "
        "| observed=no_observation | total | accuracy |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for schema in schemas_seen:
        counts = _confusion_counts(result.rows, schema)
        observable_total = 0
        correct_total = 0
        for exp in _EXPECTED:
            row_total = sum(counts.get((exp, obs), 0) for obs in _OBSERVED)
            if row_total == 0:
                continue
            cells = " | ".join(
                str(counts.get((exp, obs), 0)) for obs in _OBSERVED
            )
            observable = sum(
                counts.get((exp, obs), 0)
                for obs in (OBSERVED_REFUSE, OBSERVED_ANSWER)
            )
            correct = counts.get((exp, exp), 0)
            observable_total += observable
            correct_total += correct
            acc = f"{correct}/{observable}" if observable else "n/a"
            lines.append(
                f"| {schema} | {exp} | {cells} | {row_total} | {acc} |"
            )
        if observable_total:
            pct = 100.0 * correct_total / observable_total
            lines.append(
                f"| {schema} | **overall** |  |  |  | {observable_total} "
                f"| {correct_total}/{observable_total} ({pct:.1f}%) |"
            )
    return "\n".join(lines) + "\n"


def _write_scored_jsonl(out_path: Path, rows: list[ScoredRow]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        for r in rows:
            fp.write(
                json.dumps(
                    {
                        "rubric": r.rubric,
                        "record_id": r.record_id,
                        "schema_version": r.schema_version,
                        "question": r.question,
                        "label_id": r.label_id,
                        "expected_outcome": r.expected_outcome,
                        "observed_outcome": r.observed_outcome,
                        "mode": r.mode,
                        "match": r.match,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def cmd_score(args: argparse.Namespace) -> int:
    if args.rubric != RUBRIC:
        # Future slices will add more rubrics; for slice 3 only "refusal"
        # is wired. Reject explicitly rather than silently doing nothing.
        print(
            f"SCORE FAILED: unknown rubric {args.rubric!r}; slice 3 supports "
            f"only {RUBRIC!r}",
            file=sys.stderr,
        )
        return 2

    _repo.ensure_build_imports_on_path()
    try:
        run_startup_invariants()
    except InvariantError as exc:
        print(f"INVARIANT FAILED: {exc}", file=sys.stderr)
        return 2

    envelope_path = Path(args.ingested)
    try:
        result = score_refusal(envelope_path)
    except ScoreError as exc:
        print(f"SCORE FAILED: {exc}", file=sys.stderr)
        return 2

    if args.out:
        _write_scored_jsonl(Path(args.out), result.rows)

    if args.markdown:
        Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown).write_text(render_refusal_report(result), encoding="utf-8")

    print(render_refusal_report(result), end="")
    return 0
