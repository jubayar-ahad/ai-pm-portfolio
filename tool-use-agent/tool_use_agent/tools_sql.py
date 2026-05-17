"""Read-only SQL query tool backed by SQLite.

Accepts a repo-relative path to a SQLite database file plus a SQL string,
rejects write/DDL keywords statically (parametrized denylist), opens the
database in URI read-only mode (`mode=ro`), executes the remaining
read-only statement, and returns the result as
`{"columns": [...], "rows": [{...}, ...], "row_count": N}`.

Returns sentinel `"ERROR: ..."` strings on the failure cases an agent
could plausibly trigger (path outside repo, file missing, file not a
SQLite database, write keyword present, malformed SQL, max_rows out of
range). The agent receives these as `tool_result` content and can
recover, matching the recovery contract `tools_repo.read_repo_file`
established for this catalog.

Two-layer safety guardrail:
  Layer 1 — static keyword denylist (`WRITE_KEYWORDS`), pre-screened against
            the uppercased token stream after stripping string literals
            and SQL comments. Rejects writes BEFORE opening the database.
  Layer 2 — `sqlite3.connect("file:<path>?mode=ro", uri=True)` — even if
            a keyword slips past layer 1 (e.g. via a creative quoting
            trick), the connection itself refuses any write/DDL.

The layered design is the lock; either layer alone would be insufficient.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from tool_use_agent.tools_repo import _resolve_inside_repo

# Write / DDL / transaction keywords rejected by the static denylist. Each
# is matched as a whole word (case-insensitive) against the post-strip
# token stream. The list is conservative: VACUUM, REINDEX, PRAGMA, and
# ATTACH/DETACH can all mutate state and are denied here even though they
# would also be denied by `mode=ro`.
WRITE_KEYWORDS: frozenset[str] = frozenset({
    "INSERT", "UPDATE", "DELETE", "REPLACE", "MERGE",
    "DROP", "TRUNCATE", "ALTER", "CREATE", "RENAME",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX",
    "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE",
})

# Hard cap on rows returned, regardless of caller's `max_rows`. Keeps the
# tool's worst-case response size bounded for the agent's context budget.
ROW_CEILING = 1000


def _strip_sql_noise(sql: str) -> str:
    """Drop string literals and SQL comments from `sql` for token scanning.

    Single-quoted strings (with `''` escape), double-quoted identifiers,
    `-- line comments`, and `/* block comments */` are replaced with a
    single space so subsequent tokenization sees only the SQL skeleton.
    The output is NOT executable SQL — only suitable for keyword scans.
    """
    out: list[str] = []
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        # `-- line comment` → space, skip to end of line
        if c == "-" and i + 1 < n and sql[i + 1] == "-":
            i += 2
            while i < n and sql[i] != "\n":
                i += 1
            out.append(" ")
            continue
        # `/* block comment */` → space, skip to closing `*/`
        if c == "/" and i + 1 < n and sql[i + 1] == "*":
            i += 2
            while i + 1 < n and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2
            out.append(" ")
            continue
        # `'string literal'` (with `''` escape)
        if c == "'":
            i += 1
            while i < n:
                if sql[i] == "'" and i + 1 < n and sql[i + 1] == "'":
                    i += 2
                    continue
                if sql[i] == "'":
                    i += 1
                    break
                i += 1
            out.append(" ")
            continue
        # `"quoted identifier"` (treat like a literal for keyword scanning;
        # we don't want a column named "DROP" to trip the denylist)
        if c == '"':
            i += 1
            while i < n and sql[i] != '"':
                i += 1
            i += 1
            out.append(" ")
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _tokens(sql: str) -> list[str]:
    """Return uppercased word tokens from `sql` after stripping noise."""
    cleaned = _strip_sql_noise(sql)
    return re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", cleaned.upper())


def _statement_count(sql: str) -> int:
    """Count top-level `;`-separated, non-empty SQL statements in `sql`.

    String literals and comments are stripped first so a semicolon inside
    `'foo;bar'` does not register as a statement boundary.
    """
    cleaned = _strip_sql_noise(sql)
    return sum(1 for chunk in cleaned.split(";") if chunk.strip())


def sql_query(
    repo_root: Path,
    path: str,
    sql: str,
    max_rows: int = 100,
) -> dict[str, Any] | str:
    """Execute a read-only SQL `SELECT` against a repo-relative SQLite file.

    Layered safety: a static write-keyword denylist (`WRITE_KEYWORDS`)
    rejects mutations before the connection opens; the connection itself
    is opened in URI read-only mode (`mode=ro`) so any keyword that
    slipped past the denylist would also be refused by SQLite.

    On success: `{"columns": [...], "rows": [{...}, ...], "row_count": N}`.
    On failure: a sentinel `"ERROR: ..."` string (matches the recovery
    contract of `tools_repo.read_repo_file`).
    """
    if not isinstance(sql, str) or not sql.strip():
        return "ERROR: empty SQL string"
    if max_rows < 1:
        return f"ERROR: max_rows must be >= 1 (got {max_rows})"
    if max_rows > ROW_CEILING:
        return (
            f"ERROR: max_rows {max_rows} exceeds hard ceiling "
            f"{ROW_CEILING}"
        )
    if _statement_count(sql) > 1:
        return "ERROR: multiple statements rejected (one SELECT per call)"

    bad = sorted({t for t in _tokens(sql) if t in WRITE_KEYWORDS})
    if bad:
        return f"ERROR: write keyword(s) rejected: {bad}"

    resolved = _resolve_inside_repo(repo_root, path)
    if resolved is None:
        return f"ERROR: path {path!r} escapes the repo root"
    if not resolved.exists():
        return f"ERROR: no such file: {path!r}"
    if not resolved.is_file():
        return f"ERROR: not a regular file: {path!r}"

    uri = f"file:{resolved.as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        return f"ERROR: cannot open database: {exc}"

    try:
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql)
        except sqlite3.Error as exc:
            return f"ERROR: SQL execution failed: {exc}"
        try:
            fetched = cursor.fetchmany(max_rows)
        except sqlite3.Error as exc:
            return f"ERROR: row fetch failed: {exc}"
        columns = [desc[0] for desc in (cursor.description or [])]
        rows = [dict(row) for row in fetched]
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    finally:
        conn.close()


__all__ = [
    "ROW_CEILING",
    "WRITE_KEYWORDS",
    "sql_query",
]
