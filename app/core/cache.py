from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path


class PriceCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stooq_cache (
                    symbol TEXT NOT NULL,
                    fetch_date TEXT NOT NULL,
                    csv_data TEXT NOT NULL,
                    PRIMARY KEY(symbol, fetch_date)
                )
                """
            )

    def get_today(self, symbol: str) -> str | None:
        today = date.today().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT csv_data FROM stooq_cache WHERE symbol = ? AND fetch_date = ?",
                (symbol, today),
            ).fetchone()
            return row[0] if row else None

    def get_latest(self, symbol: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT csv_data
                FROM stooq_cache
                WHERE symbol = ?
                ORDER BY fetch_date DESC
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
            return row[0] if row else None

    def set_today(self, symbol: str, csv_data: str) -> None:
        today = date.today().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO stooq_cache(symbol, fetch_date, csv_data)
                VALUES(?, ?, ?)
                ON CONFLICT(symbol, fetch_date) DO UPDATE SET csv_data = excluded.csv_data
                """,
                (symbol, today, csv_data),
            )
