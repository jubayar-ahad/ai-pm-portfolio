"""Regenerate `fixtures/sample.db` deterministically.

The committed `sample.db` is built by this script — keep them in sync. Run
from the repo root or this directory:

    python3 tool-use-agent/fixtures/make_sample_db.py

The fixture is a tiny three-table catalog (`books`, `authors`,
`book_genres`) chosen so the `sql_query` tool can demo joins,
aggregations, and filters without external data. No PII, no opinions,
no copyrighted text — just a small bibliographic reference set.

`PRAGMA application_id` is set to a stable sentinel so `sqlite3 sample.db
".dbinfo"` or `file(1)` can confirm the fixture identity at a glance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "sample.db"

# Stable schema + rows. Adding rows is fine; reordering existing rows
# will change the committed binary, which is OK as long as the unit
# tests pin themselves to row content, not row order on disk.
SCHEMA: tuple[str, ...] = (
    """
    CREATE TABLE authors (
        id        INTEGER PRIMARY KEY,
        name      TEXT NOT NULL,
        born      INTEGER NOT NULL,
        country   TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE books (
        id        INTEGER PRIMARY KEY,
        title     TEXT NOT NULL,
        author_id INTEGER NOT NULL REFERENCES authors(id),
        year      INTEGER NOT NULL,
        pages     INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE book_genres (
        book_id   INTEGER NOT NULL REFERENCES books(id),
        genre     TEXT NOT NULL,
        PRIMARY KEY (book_id, genre)
    )
    """,
)

AUTHORS: tuple[tuple[int, str, int, str], ...] = (
    (1, "Ursula K. Le Guin", 1929, "USA"),
    (2, "Italo Calvino", 1923, "Italy"),
    (3, "Jorge Luis Borges", 1899, "Argentina"),
    (4, "Octavia Butler", 1947, "USA"),
)

BOOKS: tuple[tuple[int, str, int, int, int], ...] = (
    (1, "A Wizard of Earthsea", 1, 1968, 205),
    (2, "The Left Hand of Darkness", 1, 1969, 304),
    (3, "Invisible Cities", 2, 1972, 165),
    (4, "If on a winter's night a traveler", 2, 1979, 260),
    (5, "Ficciones", 3, 1944, 174),
    (6, "Kindred", 4, 1979, 287),
    (7, "Parable of the Sower", 4, 1993, 299),
)

BOOK_GENRES: tuple[tuple[int, str], ...] = (
    (1, "fantasy"),
    (2, "science-fiction"),
    (3, "magical-realism"),
    (4, "postmodern"),
    (5, "short-stories"),
    (5, "magical-realism"),
    (6, "science-fiction"),
    (7, "science-fiction"),
)

APPLICATION_ID = 0x54554153  # "TUAS" — Tool-Use-Agent Sample


def build(db_path: Path = DB_PATH) -> None:
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        for ddl in SCHEMA:
            conn.execute(ddl)
        conn.executemany(
            "INSERT INTO authors (id, name, born, country) VALUES (?,?,?,?)",
            AUTHORS,
        )
        conn.executemany(
            "INSERT INTO books (id, title, author_id, year, pages) "
            "VALUES (?,?,?,?,?)",
            BOOKS,
        )
        conn.executemany(
            "INSERT INTO book_genres (book_id, genre) VALUES (?,?)",
            BOOK_GENRES,
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    build()
    print(f"wrote {DB_PATH} ({DB_PATH.stat().st_size} bytes)")
