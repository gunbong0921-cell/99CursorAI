from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import DrawRecord

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS draws (
    draw_no INTEGER PRIMARY KEY,
    draw_date TEXT NOT NULL,
    n1 INTEGER NOT NULL,
    n2 INTEGER NOT NULL,
    n3 INTEGER NOT NULL,
    n4 INTEGER NOT NULL,
    n5 INTEGER NOT NULL,
    n6 INTEGER NOT NULL,
    bonus INTEGER NOT NULL,
    tot_sell_amount INTEGER,
    collected_at TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prizes (
    draw_no INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    winner_count INTEGER NOT NULL,
    win_amount INTEGER NOT NULL,
    sum_win_amount INTEGER,
    PRIMARY KEY (draw_no, rank),
    FOREIGN KEY (draw_no) REFERENCES draws(draw_no)
);

CREATE TABLE IF NOT EXISTS collect_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    fetched INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    message TEXT
);

CREATE TABLE IF NOT EXISTS collect_failures (
    draw_no INTEGER PRIMARY KEY,
    error TEXT NOT NULL,
    failed_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 1
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    return conn


def existing_draw_nos(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT draw_no FROM draws").fetchall()
    return {int(row["draw_no"]) for row in rows}


def failed_draw_nos(conn: sqlite3.Connection) -> list[int]:
    rows = conn.execute(
        "SELECT draw_no FROM collect_failures ORDER BY draw_no"
    ).fetchall()
    return [int(row["draw_no"]) for row in rows]


def draw_range(conn: sqlite3.Connection) -> tuple[int | None, int | None, int]:
    row = conn.execute(
        "SELECT MIN(draw_no) AS mn, MAX(draw_no) AS mx, COUNT(*) AS cnt FROM draws"
    ).fetchone()
    return row["mn"], row["mx"], int(row["cnt"] or 0)


def save_draw(conn: sqlite3.Connection, record: DrawRecord, collected_at: str) -> None:
    conn.execute(
        """
        INSERT INTO draws (
            draw_no, draw_date, n1, n2, n3, n4, n5, n6, bonus,
            tot_sell_amount, collected_at, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(draw_no) DO UPDATE SET
            draw_date = excluded.draw_date,
            n1 = excluded.n1,
            n2 = excluded.n2,
            n3 = excluded.n3,
            n4 = excluded.n4,
            n5 = excluded.n5,
            n6 = excluded.n6,
            bonus = excluded.bonus,
            tot_sell_amount = excluded.tot_sell_amount,
            collected_at = excluded.collected_at,
            source = excluded.source
        """,
        (
            record.draw_no,
            record.draw_date,
            *record.numbers,
            record.bonus,
            record.tot_sell_amount,
            collected_at,
            record.source,
        ),
    )
    conn.execute("DELETE FROM prizes WHERE draw_no = ?", (record.draw_no,))
    conn.executemany(
        """
        INSERT INTO prizes (draw_no, rank, winner_count, win_amount, sum_win_amount)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                record.draw_no,
                prize.rank,
                prize.winner_count,
                prize.win_amount,
                prize.sum_win_amount,
            )
            for prize in record.prizes
        ],
    )
    conn.execute("DELETE FROM collect_failures WHERE draw_no = ?", (record.draw_no,))


def record_failure(conn: sqlite3.Connection, draw_no: int, error: str) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO collect_failures (draw_no, error, failed_at, attempts)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(draw_no) DO UPDATE SET
            error = excluded.error,
            failed_at = excluded.failed_at,
            attempts = collect_failures.attempts + 1
        """,
        (draw_no, error, now),
    )


def start_log(conn: sqlite3.Connection, started_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO collect_log (started_at, message) VALUES (?, ?)",
        (started_at, "started"),
    )
    conn.commit()
    return int(cur.lastrowid)


def finish_log(
    conn: sqlite3.Connection,
    log_id: int,
    *,
    fetched: int,
    skipped: int,
    failed: int,
    message: str,
) -> None:
    conn.execute(
        """
        UPDATE collect_log
        SET ended_at = ?, fetched = ?, skipped = ?, failed = ?, message = ?
        WHERE id = ?
        """,
        (utc_now(), fetched, skipped, failed, message, log_id),
    )
    conn.commit()
