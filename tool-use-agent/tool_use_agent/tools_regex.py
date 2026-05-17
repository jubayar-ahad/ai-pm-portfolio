"""Regex extraction tool for the agent's "find places to change" workflow.

Accepts a repo-relative ``path`` (file or directory) plus a regex
``pattern``, compiles the regex, walks text files under the path, and
returns matches with line numbers and capture groups. The shape parallels
``tools_repo.grep_repo`` but adds Python ``re``-style pattern matching
(anchors, character classes, lookarounds, capture groups) so the agent
can extract structured pieces from each hit, not just confirm presence.

Two-layer safety guardrail mirroring ``sql_query`` and ``file_rewrite``:
  Layer 1 — ``re.compile`` plus a pattern-length cap. The compile
            validates pattern shape (rejects malformed regex BEFORE any
            file IO); the length cap (``MAX_PATTERN_LENGTH``) bounds the
            worst-case backtracking blast radius a pathological pattern
            could trigger.
  Layer 2 — repo-relative resolve via ``tools_repo._resolve_inside_repo``
            plus a hard ceiling on returned matches
            (``MATCH_CEILING``) plus a per-file byte cap (mirrors
            ``grep_repo`` so an oversized blob never gets scanned).

Either layer alone has a documented soft spot; together they compose
into a single hard refusal before any pathological work happens. This is
the same pattern as ``WRITE_KEYWORDS`` + ``mode=ro`` for SQL and the
operation enum + sandbox resolve for ``file_rewrite``.

Return shape on success::

    {
        "pattern": str,            # echoed
        "path": str,               # echoed
        "matches": [
            {
                "path": str,       # repo-relative file path
                "line_number": int,
                "match": str,      # the full matched substring
                "groups": [...],   # capture groups (empty list if none)
                "span": [int, int] # [start_col, end_col] on the line
            },
            ...
        ],
        "match_count": int,
        "truncated": bool,         # True if max_matches cap was hit
    }

On failure: a sentinel ``"ERROR: ..."`` string matching the recovery
contract of ``tools_repo.read_repo_file`` /
``tools_sql.sql_query`` / ``tools_rewrite.file_rewrite``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tool_use_agent.tools_repo import (
    MAX_GREP_FILE_BYTES,
    TEXT_SUFFIXES,
    _excluded,
    _resolve_inside_repo,
)

# Hard cap on regex pattern length. A pattern of >1000 chars is almost
# always a sign of paste-the-whole-file misuse, and bounds the worst-case
# backtracking blast radius for the pathological-quantifier family of
# patterns (``(a+)+b`` and friends).
MAX_PATTERN_LENGTH = 1000

# Hard ceiling on returned matches, regardless of caller's ``max_matches``.
# Keeps the tool's worst-case response size bounded for the agent's
# context budget — same shape as ``tools_sql.ROW_CEILING``.
MATCH_CEILING = 1000


def regex_extract(
    repo_root: Path,
    pattern: str,
    path: str = ".",
    max_matches: int = 20,
) -> dict[str, Any] | str:
    """Return regex matches under ``path`` with line numbers and groups.

    ``pattern`` is a Python ``re``-style regex (use ``(?i)`` for case
    insensitivity inline). ``path`` is a repo-relative file or directory;
    a directory walks all text-suffixed files under it (same suffix set
    as ``grep_repo``). ``max_matches`` caps results; ``MATCH_CEILING``
    is the absolute hard ceiling.

    The function never raises on agent-plausible failure modes (malformed
    regex, path escape, missing file, non-text file): it returns a
    sentinel ``"ERROR: ..."`` string so the agent can recover via
    ``tool_result``.
    """
    if not isinstance(pattern, str) or not pattern:
        return "ERROR: empty pattern"
    if len(pattern) > MAX_PATTERN_LENGTH:
        return (
            f"ERROR: pattern length {len(pattern)} exceeds "
            f"{MAX_PATTERN_LENGTH}-char cap"
        )
    if max_matches < 1:
        return f"ERROR: max_matches must be >= 1 (got {max_matches})"
    if max_matches > MATCH_CEILING:
        return (
            f"ERROR: max_matches {max_matches} exceeds hard ceiling "
            f"{MATCH_CEILING}"
        )

    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        return f"ERROR: invalid regex: {exc}"

    base = _resolve_inside_repo(repo_root, path)
    if base is None:
        return f"ERROR: path {path!r} escapes the repo root"
    if not base.exists():
        return f"ERROR: no such path: {path!r}"

    if base.is_file():
        candidates = [base]
    else:
        candidates = sorted(p for p in base.rglob("*") if p.is_file())

    matches: list[dict[str, Any]] = []
    truncated = False
    for file_path in candidates:
        if _excluded(file_path, repo_root):
            continue
        if file_path.suffix and file_path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            if file_path.stat().st_size > MAX_GREP_FILE_BYTES:
                continue
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = file_path.resolve().relative_to(repo_root.resolve()).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            for m in compiled.finditer(line):
                matches.append(
                    {
                        "path": rel,
                        "line_number": line_number,
                        "match": m.group(0),
                        "groups": list(m.groups()),
                        "span": list(m.span()),
                    }
                )
                if len(matches) >= max_matches:
                    truncated = True
                    return {
                        "pattern": pattern,
                        "path": path,
                        "matches": matches,
                        "match_count": len(matches),
                        "truncated": truncated,
                    }

    return {
        "pattern": pattern,
        "path": path,
        "matches": matches,
        "match_count": len(matches),
        "truncated": truncated,
    }


__all__ = [
    "MATCH_CEILING",
    "MAX_PATTERN_LENGTH",
    "regex_extract",
]
