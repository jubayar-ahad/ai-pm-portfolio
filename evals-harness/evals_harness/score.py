"""Per-rubric scorers for the evals harness (slices 3 + 4).

Reads a normalized ``ingested.jsonl`` envelope produced by ``ingest``,
joins traces to labels by (question, schema_version ∈ applies_to),
and applies a per-rubric scorer:

* ``refusal`` (cross-build, slice 3). Classifies each trace as
  ``refuse`` / ``answer`` / ``no_observation`` against the label's
  ``expected_outcome``. rag-app refuses via ``mode == "refused-low-score"``
  or ``answer.text == REFUSAL_SENTENCE``; tool-use-agent refuses via
  ``final_text == REFUSAL_SENTENCE`` cross-checked against
  ``refusal_reason`` (disagreement raises ``ScoreError``).
* ``groundedness`` (rag-app only, slice 4). For labels with
  ``expected_outcome == "answer"`` paired with rag-app traces, reads the
  trace's ``verification`` block and counts the answer as grounded iff
  ``all_resolved`` is true AND (when the label carries an
  ``expected_citation_source``) that source appears in the resolved
  citations. Refused / dry-run / verification-missing traces classify
  as ``no_observation`` and are excluded from the accuracy denominator.
* ``first_call_tool`` (tool-use-agent only, slice 4). For labels with
  a non-null ``expected_first_tool`` paired with tool-use-agent traces,
  checks whether ``tool_calls[0].tool`` matches. Empty ``tool_calls``
  (refusal, dry-run, model-answered-without-tools) classify as
  ``no_observation``.

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

RUBRIC = "refusal"  # kept for slice-3 callers; prefer the named constant below
RUBRIC_REFUSAL = "refusal"
RUBRIC_GROUNDEDNESS = "groundedness"
RUBRIC_FIRST_CALL_TOOL = "first_call_tool"
RUBRIC_TERMINATION = "termination"

ALL_RUBRICS = (
    RUBRIC_REFUSAL,
    RUBRIC_GROUNDEDNESS,
    RUBRIC_FIRST_CALL_TOOL,
    RUBRIC_TERMINATION,
)

OBSERVED_REFUSE = "refuse"
OBSERVED_ANSWER = "answer"
OBSERVED_NONE = "no_observation"

SCHEMA_RAG_APP = "rag-app.ask.v1"
SCHEMA_TOOL_USE_AGENT = "tool-use-agent.ask.v1"


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


# ---------------------------------------------------------------------------
# Groundedness rubric (rag-app only)
# ---------------------------------------------------------------------------


GROUNDED_TRUE = "grounded"
GROUNDED_FALSE = "not_grounded"
GROUNDED_NONE = "no_observation"


@dataclass(frozen=True)
class GroundednessRow:
    """One scored groundedness observation.

    ``citations_total`` / ``citations_resolved`` mirror the rag-app
    ``verification`` block. ``expected_citation_source`` is the label's
    optional pinned source (e.g. ``"OBJECTIVE.md"``);
    ``expected_source_cited`` is True iff *any* resolved citation has
    that source. ``match`` is the final per-row pass/fail used by the
    aggregate report; it is False whenever the observation is missing
    so accuracy stays a per-observed-record fraction.
    """

    rubric: str
    record_id: str
    schema_version: str
    question: str
    label_id: str
    citations_total: int
    citations_resolved: int
    all_resolved: bool
    expected_citation_source: str | None
    expected_source_cited: bool
    observed_outcome: str  # grounded / not_grounded / no_observation
    match: bool


@dataclass
class GroundednessResult:
    rows: list[GroundednessRow] = field(default_factory=list)
    n_labels: int = 0
    n_traces: int = 0
    n_unpaired_traces: int = 0
    n_unpaired_labels: int = 0


def _extract_groundedness(
    trace: dict[str, Any],
    expected_source: str | None,
) -> tuple[str, int, int, bool, bool]:
    """Return (observed_outcome, total, resolved, all_resolved, source_cited).

    ``observed_outcome`` is one of GROUNDED_TRUE / GROUNDED_FALSE /
    GROUNDED_NONE. A missing verification block (refused / dry-run /
    non-answer mode) classifies as GROUNDED_NONE and the numeric fields
    are zeroed.
    """
    verification = trace.get("verification")
    if not isinstance(verification, dict):
        return GROUNDED_NONE, 0, 0, False, False
    total = int(verification.get("total", 0) or 0)
    resolved = int(verification.get("resolved", 0) or 0)
    all_resolved = bool(verification.get("all_resolved", False))
    citations = verification.get("citations") or []
    source_cited = False
    if expected_source is not None and isinstance(citations, list):
        source_cited = any(
            isinstance(c, dict)
            and c.get("source") == expected_source
            and c.get("resolved")
            for c in citations
        )
    if not all_resolved:
        return GROUNDED_FALSE, total, resolved, all_resolved, source_cited
    if expected_source is not None and not source_cited:
        return GROUNDED_FALSE, total, resolved, all_resolved, source_cited
    return GROUNDED_TRUE, total, resolved, all_resolved, source_cited


def score_groundedness(envelope_path: Path) -> GroundednessResult:
    """Run the groundedness rubric over a normalized ingested.jsonl envelope.

    Applies only to (label.expected_outcome == "answer") paired with
    rag-app traces. Non-applicable label/trace pairs (refuse-labels,
    tool-use-agent traces, no-verification-block traces) are excluded
    from the rubric's scored rows entirely — the refusal rubric is the
    right home for those.
    """
    labels, traces = _read_envelope(envelope_path)
    labels_by_q = _index_labels_by_question(labels)

    rows: list[GroundednessRow] = []
    matched_label_ids: set[str] = set()
    unpaired_traces = 0
    eligible_traces = 0

    for trace in traces:
        schema = trace.get("schema_version")
        if schema != SCHEMA_RAG_APP:
            continue
        eligible_traces += 1
        question = trace.get("question")
        candidates = [
            lab
            for lab in labels_by_q.get(question, [])
            if schema in lab.get("applies_to", [])
            and lab.get("expected_outcome") == OBSERVED_ANSWER
        ]
        if not candidates:
            unpaired_traces += 1
            continue

        for lab in candidates:
            expected_source = lab.get("expected_citation_source")
            outcome, total, resolved, all_resolved, source_cited = (
                _extract_groundedness(trace, expected_source)
            )
            match = outcome == GROUNDED_TRUE
            rows.append(
                GroundednessRow(
                    rubric=RUBRIC_GROUNDEDNESS,
                    record_id=trace["record_id"],
                    schema_version=schema,
                    question=question,
                    label_id=lab["id"],
                    citations_total=total,
                    citations_resolved=resolved,
                    all_resolved=all_resolved,
                    expected_citation_source=expected_source,
                    expected_source_cited=source_cited,
                    observed_outcome=outcome,
                    match=match,
                )
            )
            matched_label_ids.add(lab["id"])

    # Unpaired labels: ones with expected_outcome=answer and applies_to
    # listing rag-app, but no rag-app trace surfaced them.
    eligible_labels = [
        lab
        for lab in labels
        if lab.get("expected_outcome") == OBSERVED_ANSWER
        and SCHEMA_RAG_APP in lab.get("applies_to", [])
    ]
    unpaired_labels = sum(
        1 for lab in eligible_labels if lab["id"] not in matched_label_ids
    )

    rows.sort(key=lambda r: (r.schema_version, r.record_id, r.label_id))

    return GroundednessResult(
        rows=rows,
        n_labels=len(eligible_labels),
        n_traces=eligible_traces,
        n_unpaired_traces=unpaired_traces,
        n_unpaired_labels=unpaired_labels,
    )


def render_groundedness_report(result: GroundednessResult) -> str:
    """Render a small Markdown summary of the groundedness rubric."""
    n_grounded = sum(1 for r in result.rows if r.observed_outcome == GROUNDED_TRUE)
    n_not = sum(1 for r in result.rows if r.observed_outcome == GROUNDED_FALSE)
    n_none = sum(1 for r in result.rows if r.observed_outcome == GROUNDED_NONE)
    observable = n_grounded + n_not
    lines: list[str] = []
    lines.append("# Groundedness rubric (rag-app only)")
    lines.append("")
    lines.append(
        f"applicable_labels={result.n_labels}  rag_app_traces={result.n_traces}  "
        f"scored_rows={len(result.rows)}  "
        f"unpaired_traces={result.n_unpaired_traces}  "
        f"unpaired_labels={result.n_unpaired_labels}"
    )
    lines.append("")
    if not result.rows:
        lines.append("(no paired (answer-label, rag-app trace) records — nothing to score)")
        return "\n".join(lines) + "\n"
    lines.append(
        "| build | grounded | not_grounded | no_observation | total | accuracy |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    acc = f"{n_grounded}/{observable}" if observable else "n/a"
    if observable:
        pct = 100.0 * n_grounded / observable
        acc = f"{n_grounded}/{observable} ({pct:.1f}%)"
    lines.append(
        f"| {SCHEMA_RAG_APP} | {n_grounded} | {n_not} | {n_none} "
        f"| {len(result.rows)} | {acc} |"
    )
    # Per-row not-grounded callouts so a reader can see *which* questions failed.
    failures = [r for r in result.rows if r.observed_outcome == GROUNDED_FALSE]
    if failures:
        lines.append("")
        lines.append("Not-grounded rows:")
        for r in failures:
            why = (
                f"all_resolved={r.all_resolved}, "
                f"resolved={r.citations_resolved}/{r.citations_total}"
            )
            if r.expected_citation_source is not None and not r.expected_source_cited:
                why += f", expected_source={r.expected_citation_source!r} not cited"
            lines.append(f"- {r.label_id} ({r.record_id}): {why}")
    return "\n".join(lines) + "\n"


def _write_groundedness_jsonl(
    out_path: Path, rows: list[GroundednessRow]
) -> None:
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
                        "citations_total": r.citations_total,
                        "citations_resolved": r.citations_resolved,
                        "all_resolved": r.all_resolved,
                        "expected_citation_source": r.expected_citation_source,
                        "expected_source_cited": r.expected_source_cited,
                        "observed_outcome": r.observed_outcome,
                        "match": r.match,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


# ---------------------------------------------------------------------------
# First-call tool rubric (tool-use-agent only)
# ---------------------------------------------------------------------------


FIRST_CALL_MATCH = "match"
FIRST_CALL_MISMATCH = "mismatch"
FIRST_CALL_NONE = "no_observation"


@dataclass(frozen=True)
class FirstCallToolRow:
    rubric: str
    record_id: str
    schema_version: str
    question: str
    label_id: str
    expected_first_tool: str
    observed_first_tool: str | None
    observed_outcome: str  # match / mismatch / no_observation
    match: bool


@dataclass
class FirstCallToolResult:
    rows: list[FirstCallToolRow] = field(default_factory=list)
    n_labels: int = 0
    n_traces: int = 0
    n_unpaired_traces: int = 0
    n_unpaired_labels: int = 0


def _extract_first_tool(trace: dict[str, Any]) -> str | None:
    """Return tool_calls[0].tool, or None if no tool calls were made."""
    calls = trace.get("tool_calls")
    if not isinstance(calls, list) or not calls:
        return None
    first = calls[0]
    if not isinstance(first, dict):
        return None
    tool = first.get("tool")
    return tool if isinstance(tool, str) else None


def score_first_call_tool(envelope_path: Path) -> FirstCallToolResult:
    """Run the first-call tool rubric over a normalized ingested.jsonl envelope.

    Applies only to (label.expected_first_tool != null) paired with
    tool-use-agent traces. Empty tool_calls (refusal / dry-run /
    model-answered-without-tools) classify as ``no_observation`` and are
    excluded from the accuracy denominator.
    """
    labels, traces = _read_envelope(envelope_path)
    labels_by_q = _index_labels_by_question(labels)

    rows: list[FirstCallToolRow] = []
    matched_label_ids: set[str] = set()
    unpaired_traces = 0
    eligible_traces = 0

    for trace in traces:
        schema = trace.get("schema_version")
        if schema != SCHEMA_TOOL_USE_AGENT:
            continue
        eligible_traces += 1
        question = trace.get("question")
        candidates = [
            lab
            for lab in labels_by_q.get(question, [])
            if schema in lab.get("applies_to", [])
            and lab.get("expected_first_tool") is not None
        ]
        if not candidates:
            unpaired_traces += 1
            continue

        observed = _extract_first_tool(trace)
        for lab in candidates:
            expected = lab["expected_first_tool"]
            if observed is None:
                outcome = FIRST_CALL_NONE
                match = False
            elif observed == expected:
                outcome = FIRST_CALL_MATCH
                match = True
            else:
                outcome = FIRST_CALL_MISMATCH
                match = False
            rows.append(
                FirstCallToolRow(
                    rubric=RUBRIC_FIRST_CALL_TOOL,
                    record_id=trace["record_id"],
                    schema_version=schema,
                    question=question,
                    label_id=lab["id"],
                    expected_first_tool=expected,
                    observed_first_tool=observed,
                    observed_outcome=outcome,
                    match=match,
                )
            )
            matched_label_ids.add(lab["id"])

    eligible_labels = [
        lab
        for lab in labels
        if lab.get("expected_first_tool") is not None
        and SCHEMA_TOOL_USE_AGENT in lab.get("applies_to", [])
    ]
    unpaired_labels = sum(
        1 for lab in eligible_labels if lab["id"] not in matched_label_ids
    )

    rows.sort(key=lambda r: (r.schema_version, r.record_id, r.label_id))

    return FirstCallToolResult(
        rows=rows,
        n_labels=len(eligible_labels),
        n_traces=eligible_traces,
        n_unpaired_traces=unpaired_traces,
        n_unpaired_labels=unpaired_labels,
    )


def render_first_call_tool_report(result: FirstCallToolResult) -> str:
    n_match = sum(1 for r in result.rows if r.observed_outcome == FIRST_CALL_MATCH)
    n_mismatch = sum(
        1 for r in result.rows if r.observed_outcome == FIRST_CALL_MISMATCH
    )
    n_none = sum(1 for r in result.rows if r.observed_outcome == FIRST_CALL_NONE)
    observable = n_match + n_mismatch
    lines: list[str] = []
    lines.append("# First-call tool rubric (tool-use-agent only)")
    lines.append("")
    lines.append(
        f"applicable_labels={result.n_labels}  tua_traces={result.n_traces}  "
        f"scored_rows={len(result.rows)}  "
        f"unpaired_traces={result.n_unpaired_traces}  "
        f"unpaired_labels={result.n_unpaired_labels}"
    )
    lines.append("")
    if not result.rows:
        lines.append(
            "(no paired (first-tool-label, tool-use-agent trace) records — "
            "nothing to score)"
        )
        return "\n".join(lines) + "\n"
    lines.append(
        "| build | match | mismatch | no_observation | total | accuracy |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    if observable:
        pct = 100.0 * n_match / observable
        acc = f"{n_match}/{observable} ({pct:.1f}%)"
    else:
        acc = "n/a"
    lines.append(
        f"| {SCHEMA_TOOL_USE_AGENT} | {n_match} | {n_mismatch} | {n_none} "
        f"| {len(result.rows)} | {acc} |"
    )
    failures = [
        r
        for r in result.rows
        if r.observed_outcome in (FIRST_CALL_MISMATCH, FIRST_CALL_NONE)
    ]
    if failures:
        lines.append("")
        lines.append("Mismatches / missing-first-call rows:")
        for r in failures:
            obs = r.observed_first_tool if r.observed_first_tool is not None else "<none>"
            lines.append(
                f"- {r.label_id} ({r.record_id}): expected={r.expected_first_tool!r} "
                f"observed={obs!r}"
            )
    return "\n".join(lines) + "\n"


def _write_first_call_tool_jsonl(
    out_path: Path, rows: list[FirstCallToolRow]
) -> None:
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
                        "expected_first_tool": r.expected_first_tool,
                        "observed_first_tool": r.observed_first_tool,
                        "observed_outcome": r.observed_outcome,
                        "match": r.match,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


# ---------------------------------------------------------------------------
# Termination rubric (tool-use-agent only)
# ---------------------------------------------------------------------------


TERMINATION_CLEAN = "ended_clean"
TERMINATION_MODEL_REFUSED = "model_refused"
TERMINATION_MAX_STEPS = "max_steps_exhausted"
TERMINATION_REPEATED_ERROR = "repeated_tool_error"
TERMINATION_NONE = "no_observation"

_TERMINATION_BUCKETS = (
    TERMINATION_CLEAN,
    TERMINATION_MODEL_REFUSED,
    TERMINATION_MAX_STEPS,
    TERMINATION_REPEATED_ERROR,
    TERMINATION_NONE,
)


@dataclass(frozen=True)
class TerminationRow:
    """One scored termination-quality observation.

    ``observed_outcome`` is one of the five ``TERMINATION_*`` buckets:
    ``ended_clean`` is the success case (``stop_reason=end_turn`` and
    ``refusal_reason=null``); ``model_refused`` /
    ``max_steps_exhausted`` / ``repeated_tool_error`` mirror the
    tool-use-agent ``refusal_reason`` enum from slice 4; and
    ``no_observation`` covers dry-run / non-live traces. ``match`` is
    True iff observed == ``ended_clean`` (these are
    ``expected_outcome=answer`` labels — the refusal rubric scores
    refuse-labels).
    """

    rubric: str
    record_id: str
    schema_version: str
    question: str
    label_id: str
    stop_reason: str | None
    refusal_reason: str | None
    steps_taken: int | None
    max_steps: int | None
    observed_outcome: str
    match: bool


@dataclass
class TerminationResult:
    rows: list[TerminationRow] = field(default_factory=list)
    n_labels: int = 0
    n_traces: int = 0
    n_unpaired_traces: int = 0
    n_unpaired_labels: int = 0


def _extract_termination(trace: dict[str, Any]) -> tuple[str, str | None, str | None, int | None, int | None]:
    """Return (observed_outcome, stop_reason, refusal_reason, steps_taken, max_steps).

    Dry-run / non-live traces classify as ``no_observation`` with the
    raw signal fields preserved for the row record. If
    ``refusal_reason`` is set, it is the canonical observed outcome:
    cross-check that it agrees with the enumerated bucket and otherwise
    raise ``ScoreError`` (a divergence is a build bug — the slice-4
    contract requires the two signals to agree).
    """
    mode = trace.get("mode")
    stop_reason = trace.get("stop_reason")
    refusal_reason = trace.get("refusal_reason")
    steps_taken = trace.get("steps_taken")
    max_steps = trace.get("max_steps")
    steps_taken = steps_taken if isinstance(steps_taken, int) else None
    max_steps = max_steps if isinstance(max_steps, int) else None

    if mode != "live":
        return TERMINATION_NONE, stop_reason, refusal_reason, steps_taken, max_steps
    if refusal_reason is None:
        if stop_reason == "end_turn":
            return (
                TERMINATION_CLEAN,
                stop_reason,
                refusal_reason,
                steps_taken,
                max_steps,
            )
        # Live, no refusal_reason, but stop_reason isn't end_turn —
        # the build's contract says these two signals agree. Treat the
        # absence of refusal_reason as authoritative (the model emitted
        # an end_turn-equivalent) but flag it: this should not happen
        # for the current set of stop_reason values, so raise.
        rid = trace.get("record_id", "?")
        raise ScoreError(
            f"tool-use-agent trace {rid}: refusal_reason is null but "
            f"stop_reason={stop_reason!r}; expected stop_reason='end_turn' "
            f"when no refusal — build contract violation"
        )
    # refusal_reason is set; it dictates the bucket.
    bucket_map = {
        "model_refused": TERMINATION_MODEL_REFUSED,
        "max_steps_exhausted": TERMINATION_MAX_STEPS,
        "repeated_tool_error": TERMINATION_REPEATED_ERROR,
    }
    bucket = bucket_map.get(refusal_reason)
    if bucket is None:
        rid = trace.get("record_id", "?")
        raise ScoreError(
            f"tool-use-agent trace {rid}: unknown refusal_reason "
            f"{refusal_reason!r}; expected one of "
            f"{sorted(bucket_map)} or null"
        )
    return bucket, stop_reason, refusal_reason, steps_taken, max_steps


def score_termination(envelope_path: Path) -> TerminationResult:
    """Run the termination rubric over a normalized ingested.jsonl envelope.

    Applies only to (label.expected_outcome == "answer") paired with
    tool-use-agent traces. Refuse-labels are out of scope — the refusal
    rubric (slice 3) is the right home for them. Dry-run traces
    classify as ``no_observation`` and are excluded from the accuracy
    denominator (mirrors slices 3 and 4).
    """
    labels, traces = _read_envelope(envelope_path)
    labels_by_q = _index_labels_by_question(labels)

    rows: list[TerminationRow] = []
    matched_label_ids: set[str] = set()
    unpaired_traces = 0
    eligible_traces = 0

    for trace in traces:
        schema = trace.get("schema_version")
        if schema != SCHEMA_TOOL_USE_AGENT:
            continue
        eligible_traces += 1
        question = trace.get("question")
        candidates = [
            lab
            for lab in labels_by_q.get(question, [])
            if schema in lab.get("applies_to", [])
            and lab.get("expected_outcome") == OBSERVED_ANSWER
        ]
        if not candidates:
            unpaired_traces += 1
            continue

        outcome, stop_reason, refusal_reason, steps_taken, max_steps = (
            _extract_termination(trace)
        )
        for lab in candidates:
            match = outcome == TERMINATION_CLEAN
            rows.append(
                TerminationRow(
                    rubric=RUBRIC_TERMINATION,
                    record_id=trace["record_id"],
                    schema_version=schema,
                    question=question,
                    label_id=lab["id"],
                    stop_reason=stop_reason,
                    refusal_reason=refusal_reason,
                    steps_taken=steps_taken,
                    max_steps=max_steps,
                    observed_outcome=outcome,
                    match=match,
                )
            )
            matched_label_ids.add(lab["id"])

    eligible_labels = [
        lab
        for lab in labels
        if lab.get("expected_outcome") == OBSERVED_ANSWER
        and SCHEMA_TOOL_USE_AGENT in lab.get("applies_to", [])
    ]
    unpaired_labels = sum(
        1 for lab in eligible_labels if lab["id"] not in matched_label_ids
    )

    rows.sort(key=lambda r: (r.schema_version, r.record_id, r.label_id))

    return TerminationResult(
        rows=rows,
        n_labels=len(eligible_labels),
        n_traces=eligible_traces,
        n_unpaired_traces=unpaired_traces,
        n_unpaired_labels=unpaired_labels,
    )


def render_termination_report(result: TerminationResult) -> str:
    counts = {b: 0 for b in _TERMINATION_BUCKETS}
    for r in result.rows:
        counts[r.observed_outcome] += 1
    observable = sum(counts[b] for b in _TERMINATION_BUCKETS if b != TERMINATION_NONE)
    n_clean = counts[TERMINATION_CLEAN]
    lines: list[str] = []
    lines.append("# Termination rubric (tool-use-agent only)")
    lines.append("")
    lines.append(
        f"applicable_labels={result.n_labels}  tua_traces={result.n_traces}  "
        f"scored_rows={len(result.rows)}  "
        f"unpaired_traces={result.n_unpaired_traces}  "
        f"unpaired_labels={result.n_unpaired_labels}"
    )
    lines.append("")
    if not result.rows:
        lines.append(
            "(no paired (answer-label, tool-use-agent trace) records — "
            "nothing to score)"
        )
        return "\n".join(lines) + "\n"
    lines.append(
        "| build | ended_clean | model_refused | max_steps_exhausted "
        "| repeated_tool_error | no_observation | total | accuracy |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    if observable:
        pct = 100.0 * n_clean / observable
        acc = f"{n_clean}/{observable} ({pct:.1f}%)"
    else:
        acc = "n/a"
    lines.append(
        f"| {SCHEMA_TOOL_USE_AGENT} | {counts[TERMINATION_CLEAN]} "
        f"| {counts[TERMINATION_MODEL_REFUSED]} "
        f"| {counts[TERMINATION_MAX_STEPS]} "
        f"| {counts[TERMINATION_REPEATED_ERROR]} "
        f"| {counts[TERMINATION_NONE]} | {len(result.rows)} | {acc} |"
    )
    # Per-row failure callouts so a reader can see which questions
    # ended in which non-clean bucket.
    failures = [
        r
        for r in result.rows
        if r.observed_outcome != TERMINATION_CLEAN
        and r.observed_outcome != TERMINATION_NONE
    ]
    if failures:
        lines.append("")
        lines.append("Non-clean terminations:")
        for r in failures:
            step_info = (
                f"steps_taken={r.steps_taken}/{r.max_steps}"
                if r.steps_taken is not None and r.max_steps is not None
                else "steps_taken=?"
            )
            lines.append(
                f"- {r.label_id} ({r.record_id}): {r.observed_outcome} "
                f"({step_info})"
            )
    return "\n".join(lines) + "\n"


def _write_termination_jsonl(out_path: Path, rows: list[TerminationRow]) -> None:
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
                        "stop_reason": r.stop_reason,
                        "refusal_reason": r.refusal_reason,
                        "steps_taken": r.steps_taken,
                        "max_steps": r.max_steps,
                        "observed_outcome": r.observed_outcome,
                        "match": r.match,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------


def cmd_score(args: argparse.Namespace) -> int:
    if args.rubric not in ALL_RUBRICS:
        print(
            f"SCORE FAILED: unknown rubric {args.rubric!r}; supported: "
            f"{', '.join(ALL_RUBRICS)}",
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
        if args.rubric == RUBRIC_REFUSAL:
            result = score_refusal(envelope_path)
            report = render_refusal_report(result)
            if args.out:
                _write_scored_jsonl(Path(args.out), result.rows)
        elif args.rubric == RUBRIC_GROUNDEDNESS:
            g_result = score_groundedness(envelope_path)
            report = render_groundedness_report(g_result)
            if args.out:
                _write_groundedness_jsonl(Path(args.out), g_result.rows)
        elif args.rubric == RUBRIC_FIRST_CALL_TOOL:
            f_result = score_first_call_tool(envelope_path)
            report = render_first_call_tool_report(f_result)
            if args.out:
                _write_first_call_tool_jsonl(Path(args.out), f_result.rows)
        else:  # RUBRIC_TERMINATION
            t_result = score_termination(envelope_path)
            report = render_termination_report(t_result)
            if args.out:
                _write_termination_jsonl(Path(args.out), t_result.rows)
    except ScoreError as exc:
        print(f"SCORE FAILED: {exc}", file=sys.stderr)
        return 2

    if args.markdown:
        Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown).write_text(report, encoding="utf-8")

    print(report, end="")
    return 0
