"""Read-only tools over the interview-pipeline tracker.

The tracker lives at `templates/INTERVIEW_TRACKER.md` and uses a fixed
markdown-table schema locked in DECISIONS.md (stage vocabulary, B1/B2/B3
buckets). These tools parse the "Active pipeline" table, filter out
placeholder rows (`_<...>_` italicized markers), and expose rollups.

`list_pipeline_rows` returns the rows themselves; `count_by_stage` and
`count_by_bucket` are convenience histograms that an agent can call directly
instead of re-deriving the counts from `list_pipeline_rows`. All three return
empty / zero output when the tracker contains only placeholders, which is
the intended state until the user fills it in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TRACKER_RELATIVE_PATH = "templates/INTERVIEW_TRACKER.md"

ACTIVE_HEADING = "## Active pipeline"
# Anything starting with "## " (a new H2) ends the section, but only `## `
# from column 0 — not a Markdown-table cell that happens to contain `##`.
_NEXT_H2_RE = re.compile(r"^##\s+", re.MULTILINE)
_PLACEHOLDER_RE = re.compile(r"^_<.*>_$")

# Stage and bucket vocab mirrored from DECISIONS.md / INTERVIEW_TRACKER.md.
ACTIVE_STAGES = (
    "sourced", "applied", "recruiter-screen", "hiring-manager",
    "panel", "final", "offer-verbal", "offer-written", "accepted",
)
TERMINAL_STAGES = ("rejected", "withdrew", "ghosted-30d")
ALL_STAGES = ACTIVE_STAGES + TERMINAL_STAGES
BUCKETS = ("B1", "B2", "B3")


@dataclass(frozen=True)
class PipelineRow:
    row_number: str
    company: str
    role_title: str
    bucket: str
    source: str
    stage: str
    next_action: str
    due: str
    comp_range: str
    jd_link: str
    contact: str
    notes: str


def _read_tracker(repo_root: Path) -> str:
    path = repo_root / TRACKER_RELATIVE_PATH
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_active_table(tracker_text: str) -> str:
    """Slice out the lines between '## Active pipeline' and the next H2.

    Returns the empty string if the heading is missing.
    """
    start = tracker_text.find(ACTIVE_HEADING)
    if start == -1:
        return ""
    rest = tracker_text[start + len(ACTIVE_HEADING):]
    next_h2 = _NEXT_H2_RE.search(rest)
    return rest if next_h2 is None else rest[:next_h2.start()]


def _parse_rows(section: str) -> list[PipelineRow]:
    """Parse markdown-table rows out of the active-pipeline section."""
    rows: list[PipelineRow] = []
    seen_header = False
    seen_separator = False
    for raw in section.splitlines():
        line = raw.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if not seen_separator:
            # The markdown-table separator row: |---|---|...
            seen_separator = all(set(c) <= set("-: ") for c in cells)
            if seen_separator:
                continue
            # No separator? Tracker is malformed; bail.
            return []
        # Pad/trim to 12 columns to tolerate ragged tracker edits.
        cells = (cells + [""] * 12)[:12]
        company = cells[1]
        if _PLACEHOLDER_RE.match(company):
            continue
        if not company:
            continue
        rows.append(PipelineRow(
            row_number=cells[0],
            company=company,
            role_title=cells[2],
            bucket=cells[3],
            source=cells[4],
            stage=cells[5],
            next_action=cells[6],
            due=cells[7],
            comp_range=cells[8],
            jd_link=cells[9],
            contact=cells[10],
            notes=cells[11],
        ))
    return rows


def list_pipeline_rows(
    repo_root: Path,
    stage: str | None = None,
    bucket: str | None = None,
) -> list[PipelineRow]:
    """Return active-pipeline rows, optionally filtered by stage/bucket.

    Placeholder rows (`_<...>_` company markers, or empty company cells) are
    excluded. Unknown stage/bucket filter values return an empty list rather
    than raising — the agent gets a clean "no matches" signal.
    """
    if stage is not None and stage not in ALL_STAGES:
        return []
    if bucket is not None and bucket not in BUCKETS:
        return []
    text = _read_tracker(repo_root)
    if not text:
        return []
    section = _extract_active_table(text)
    rows = _parse_rows(section)
    if stage is not None:
        rows = [r for r in rows if r.stage == stage]
    if bucket is not None:
        rows = [r for r in rows if r.bucket == bucket]
    return rows


def count_by_stage(repo_root: Path) -> dict[str, int]:
    """Histogram of active-pipeline rows by stage.

    All locked stage strings appear as keys (zero counts included) so the
    output schema is stable across runs. Unknown stage strings in the
    tracker get bucketed under their literal value so the agent can surface
    typos rather than silently dropping them.
    """
    counts: dict[str, int] = {stage: 0 for stage in ALL_STAGES}
    for row in list_pipeline_rows(repo_root):
        counts[row.stage] = counts.get(row.stage, 0) + 1
    return counts


def count_by_bucket(repo_root: Path) -> dict[str, int]:
    """Histogram of active-pipeline rows by bucket (B1/B2/B3)."""
    counts: dict[str, int] = {bucket: 0 for bucket in BUCKETS}
    for row in list_pipeline_rows(repo_root):
        counts[row.bucket] = counts.get(row.bucket, 0) + 1
    return counts
