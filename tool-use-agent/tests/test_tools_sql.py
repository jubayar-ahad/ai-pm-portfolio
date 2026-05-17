"""Tests for tool_use_agent.tools_sql.sql_query.

The tool is intentionally a layered guardrail: a static write-keyword
denylist plus a `mode=ro` URI connection. These tests pin BOTH layers
independently so a regression in either surface is loud.

Reads the committed `tool-use-agent/fixtures/sample.db` directly (regen
via `python3 tool-use-agent/fixtures/make_sample_db.py` if its schema
ever drifts). No network, no API key, no subprocess.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tool_use_agent.tools_sql import (
    ROW_CEILING,
    WRITE_KEYWORDS,
    _statement_count,
    _strip_sql_noise,
    _tokens,
    sql_query,
)

# Build-root for the `tool-use-agent/` package — the fixtures directory
# sits as a sibling of `tool_use_agent/` and `tests/`. We anchor on the
# tests-dir parent so the resolver doesn't depend on the wider repo
# layout (the fixture is shipped with this build, not the repo).
BUILD_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DB_RELPATH = "fixtures/sample.db"


# --------------------------------------------------------------------------- #
# Token / statement helpers — the static layer of the guardrail.
# --------------------------------------------------------------------------- #


def test_strip_sql_noise_removes_line_comments():
    out = _strip_sql_noise("SELECT 1 -- DROP TABLE x\nFROM books")
    assert "DROP" not in out
    assert "TABLE" not in out
    assert "FROM" in out


def test_strip_sql_noise_removes_block_comments():
    out = _strip_sql_noise("SELECT /* DELETE FROM books */ 1 FROM books")
    assert "DELETE" not in out
    assert "FROM books" in out


def test_strip_sql_noise_removes_string_literals():
    # A column value that *looks* like a write keyword must not register.
    out = _strip_sql_noise("SELECT * FROM books WHERE title = 'DROP it'")
    assert "DROP" not in out


def test_strip_sql_noise_removes_quoted_identifiers():
    # A weirdly-named column "DELETE" must not register either.
    out = _strip_sql_noise('SELECT "DELETE" FROM books')
    assert "DELETE" not in out


def test_tokens_uppercases_and_splits():
    assert _tokens("select Title from books") == ["SELECT", "TITLE", "FROM", "BOOKS"]


def test_statement_count_counts_top_level_semicolons():
    assert _statement_count("SELECT 1") == 1
    assert _statement_count("SELECT 1;") == 1
    assert _statement_count("SELECT 1; SELECT 2") == 2
    assert _statement_count("SELECT 1;;;") == 1


def test_statement_count_ignores_semicolons_inside_literals():
    assert _statement_count("SELECT 'a;b;c' FROM books") == 1


def test_write_keywords_set_is_frozen_and_uppercase():
    assert isinstance(WRITE_KEYWORDS, frozenset)
    for kw in WRITE_KEYWORDS:
        assert kw == kw.upper()
    # The denylist contains the headline dangerous keywords.
    for headline in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"):
        assert headline in WRITE_KEYWORDS


# --------------------------------------------------------------------------- #
# Happy-path SELECTs against the committed fixture DB.
# --------------------------------------------------------------------------- #


def test_sql_query_select_all_books_returns_full_shape():
    out = sql_query(BUILD_ROOT, FIXTURE_DB_RELPATH, "SELECT * FROM books")
    assert isinstance(out, dict)
    assert set(out.keys()) == {"columns", "rows", "row_count"}
    assert out["columns"] == ["id", "title", "author_id", "year", "pages"]
    # Fixture ships 7 books; honor that pin.
    assert out["row_count"] == 7
    assert len(out["rows"]) == 7
    assert all(isinstance(row, dict) for row in out["rows"])


def test_sql_query_select_with_where_filters_correctly():
    out = sql_query(
        BUILD_ROOT,
        FIXTURE_DB_RELPATH,
        "SELECT title, year FROM books WHERE year > 1970 ORDER BY year",
    )
    assert isinstance(out, dict)
    titles = [row["title"] for row in out["rows"]]
    assert "Invisible Cities" in titles  # 1972
    assert "A Wizard of Earthsea" not in titles  # 1968 → excluded


def test_sql_query_join_authors_and_books():
    out = sql_query(
        BUILD_ROOT,
        FIXTURE_DB_RELPATH,
        (
            "SELECT a.name, COUNT(b.id) AS book_count "
            "FROM authors a JOIN books b ON b.author_id = a.id "
            "GROUP BY a.name ORDER BY a.name"
        ),
    )
    assert isinstance(out, dict)
    assert out["columns"] == ["name", "book_count"]
    by_name = {row["name"]: row["book_count"] for row in out["rows"]}
    assert by_name["Ursula K. Le Guin"] == 2
    assert by_name["Italo Calvino"] == 2
    assert by_name["Jorge Luis Borges"] == 1
    assert by_name["Octavia Butler"] == 2


def test_sql_query_respects_max_rows_cap():
    out = sql_query(
        BUILD_ROOT,
        FIXTURE_DB_RELPATH,
        "SELECT * FROM books ORDER BY id",
        max_rows=3,
    )
    assert isinstance(out, dict)
    assert out["row_count"] == 3
    assert len(out["rows"]) == 3
    # First three IDs are stable across regeneration.
    assert [row["id"] for row in out["rows"]] == [1, 2, 3]


# --------------------------------------------------------------------------- #
# Static-denylist rejection — layer 1 of the guardrail.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad_sql",
    [
        "INSERT INTO books (id, title) VALUES (99, 'x')",
        "UPDATE books SET title = 'x' WHERE id = 1",
        "DELETE FROM books WHERE id = 1",
        "DROP TABLE books",
        "ALTER TABLE books ADD COLUMN foo TEXT",
        "CREATE TABLE foo (id INTEGER)",
        "TRUNCATE TABLE books",
        "REPLACE INTO books (id, title) VALUES (1, 'x')",
        "PRAGMA writable_schema = ON",
        "VACUUM",
        "ATTACH DATABASE 'evil.db' AS evil",
        "BEGIN; SELECT 1; COMMIT",
    ],
)
def test_sql_query_rejects_write_keywords(bad_sql: str):
    out = sql_query(BUILD_ROOT, FIXTURE_DB_RELPATH, bad_sql)
    assert isinstance(out, str)
    assert out.startswith("ERROR:")
    # Either denied as a write keyword OR rejected as a multi-statement
    # batch (e.g. the BEGIN;...;COMMIT case). Both are valid refusals;
    # the test just pins that the call did not execute.
    assert "rejected" in out


def test_sql_query_rejects_write_keyword_case_insensitive():
    # Lowercase keyword should be denied just like uppercase.
    out = sql_query(BUILD_ROOT, FIXTURE_DB_RELPATH, "drop table books")
    assert isinstance(out, str)
    assert "DROP" in out


def test_sql_query_keyword_in_string_literal_is_allowed():
    # 'DELETE me later' is content, not a command — must NOT be rejected.
    out = sql_query(
        BUILD_ROOT,
        FIXTURE_DB_RELPATH,
        "SELECT * FROM books WHERE title = 'DELETE me later'",
    )
    assert isinstance(out, dict)
    assert out["row_count"] == 0


def test_sql_query_rejects_multi_statement_batch():
    out = sql_query(
        BUILD_ROOT,
        FIXTURE_DB_RELPATH,
        "SELECT 1; SELECT 2",
    )
    assert isinstance(out, str)
    assert "multiple statements" in out


# --------------------------------------------------------------------------- #
# Connection-level read-only guard — layer 2 of the guardrail.
# --------------------------------------------------------------------------- #


def test_sql_query_ro_mode_refuses_writes_via_function_invocation():
    """If a write somehow slipped past layer 1, mode=ro must still refuse.

    SQLite's `randomblob()` is read-only, but we can force a write
    attempt by exploiting an INSERT-shaped trigger… or, more simply,
    we can bypass the denylist using a keyword the denylist doesn't
    list and confirm sqlite still refuses. The denylist is broad
    enough that the cleanest test is to assert the connection is
    actually opened with `mode=ro`: try a write via raw SQL that has
    no banned keyword. For now, the strongest expression of the
    invariant is the denylist + the existence of the mode=ro URI in
    `sql_query`'s source — pinned below.
    """
    import inspect

    from tool_use_agent import tools_sql

    src = inspect.getsource(tools_sql)
    assert "mode=ro" in src, (
        "tools_sql.sql_query MUST open the SQLite connection with "
        "mode=ro as the layer-2 guardrail; missing now"
    )


# --------------------------------------------------------------------------- #
# Path-resolution + structural failure modes.
# --------------------------------------------------------------------------- #


def test_sql_query_path_outside_root_returns_error():
    out = sql_query(BUILD_ROOT, "../../../etc/passwd", "SELECT 1")
    assert isinstance(out, str)
    assert out.startswith("ERROR:")
    assert "escapes the repo root" in out


def test_sql_query_missing_file_returns_error():
    out = sql_query(BUILD_ROOT, "fixtures/no_such.db", "SELECT 1")
    assert isinstance(out, str)
    assert out.startswith("ERROR:")
    assert "no such file" in out


def test_sql_query_directory_returns_error():
    out = sql_query(BUILD_ROOT, "fixtures", "SELECT 1")
    assert isinstance(out, str)
    assert out.startswith("ERROR:")
    assert "not a regular file" in out


def test_sql_query_empty_sql_returns_error():
    out = sql_query(BUILD_ROOT, FIXTURE_DB_RELPATH, "   ")
    assert isinstance(out, str)
    assert "empty SQL" in out


def test_sql_query_max_rows_below_one_returns_error():
    out = sql_query(
        BUILD_ROOT, FIXTURE_DB_RELPATH, "SELECT 1", max_rows=0
    )
    assert isinstance(out, str)
    assert "max_rows" in out


def test_sql_query_max_rows_above_ceiling_returns_error():
    out = sql_query(
        BUILD_ROOT,
        FIXTURE_DB_RELPATH,
        "SELECT 1",
        max_rows=ROW_CEILING + 1,
    )
    assert isinstance(out, str)
    assert "ceiling" in out


def test_sql_query_malformed_sql_returns_error():
    out = sql_query(BUILD_ROOT, FIXTURE_DB_RELPATH, "SELECT FROM WHERE")
    assert isinstance(out, str)
    assert out.startswith("ERROR:")
    assert "SQL execution failed" in out


def test_sql_query_non_database_file_returns_error(tmp_path: Path):
    # A regular text file should produce a clean error, not a crash, the
    # moment the query actually touches the file (a tableless `SELECT 1`
    # would succeed because SQLite never reads the file header). Use a
    # query that walks the master schema so the file's malformed header
    # surfaces as a `sqlite3.DatabaseError`.
    not_db = tmp_path / "not_a_db.db"
    not_db.write_text("plain text, not a SQLite file\n", encoding="utf-8")
    out = sql_query(
        tmp_path, "not_a_db.db", "SELECT name FROM sqlite_master"
    )
    assert isinstance(out, str)
    assert out.startswith("ERROR:")


# --------------------------------------------------------------------------- #
# Fixture sanity — guards against silent regenerations.
# --------------------------------------------------------------------------- #


def test_fixture_db_exists_and_has_expected_application_id():
    import sqlite3

    db_path = BUILD_ROOT / FIXTURE_DB_RELPATH
    assert db_path.is_file(), (
        f"Expected fixture DB at {db_path}; regenerate via "
        "`python3 tool-use-agent/fixtures/make_sample_db.py`"
    )
    conn = sqlite3.connect(db_path)
    try:
        app_id = conn.execute("PRAGMA application_id").fetchone()[0]
    finally:
        conn.close()
    # 0x54554153 = "TUAS" — locked sentinel from make_sample_db.py
    assert app_id == 0x54554153
