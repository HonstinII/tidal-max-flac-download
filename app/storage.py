from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .environment import app_data_dir


def default_database_path() -> Path:
    return app_data_dir() / "tidal-max-flac-studio.db"


class AppDatabase:
    def __init__(self, path: Path | None = None):
        self.path = path or default_database_path()

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS download_runs(
                  id TEXT PRIMARY KEY,
                  created_at REAL NOT NULL,
                  completed_at REAL,
                  status TEXT NOT NULL,
                  output_dir TEXT NOT NULL,
                  options_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS queue_items(
                  id TEXT PRIMARY KEY,
                  run_id TEXT NOT NULL,
                  source_url TEXT NOT NULL,
                  source_kind TEXT,
                  source_id TEXT,
                  track_id TEXT,
                  title TEXT,
                  artist TEXT,
                  album_title TEXT,
                  album_artist TEXT,
                  album_year TEXT,
                  track_number INTEGER,
                  cover_id TEXT,
                  output_path TEXT,
                  status TEXT NOT NULL,
                  progress_current INTEGER DEFAULT 0,
                  progress_total INTEGER DEFAULT 0,
                  attempts INTEGER DEFAULT 0,
                  error TEXT,
                  created_at REAL NOT NULL,
                  updated_at REAL NOT NULL,
                  FOREIGN KEY(run_id) REFERENCES download_runs(id)
                );

                CREATE TABLE IF NOT EXISTS settings(
                  key TEXT PRIMARY KEY,
                  value_json TEXT NOT NULL
                );
                """
            )

    def table_names(self) -> set[str]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        return {row["name"] for row in rows}

    def create_run(
        self,
        run_id: str,
        status: str,
        output_dir: str,
        options: dict[str, Any],
    ) -> dict:
        now = time.time()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO download_runs(id, created_at, status, output_dir, options_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, now, status, output_dir, json.dumps(options)),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM download_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        return self._run_from_row(row) if row else None

    def list_runs(self, limit: int = 25) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM download_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._run_from_row(row) for row in rows]

    def update_run(self, run_id: str, **fields) -> dict | None:
        if not fields:
            return self.get_run(run_id)
        allowed = {"status", "completed_at", "output_dir", "options_json"}
        assignments = []
        values = []
        for key, value in fields.items():
            if key == "options":
                key = "options_json"
                value = json.dumps(value)
            if key not in allowed:
                raise ValueError(f"Unsupported run field: {key}")
            assignments.append(f"{key} = ?")
            values.append(value)
        values.append(run_id)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE download_runs SET {', '.join(assignments)} WHERE id = ?",
                values,
            )
        return self.get_run(run_id)

    def create_queue_item(
        self,
        item_id: str,
        run_id: str,
        source_url: str,
        track: dict[str, Any],
        status: str = "ready",
        source_kind: str | None = None,
        source_id: str | None = None,
    ) -> dict:
        now = time.time()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO queue_items(
                  id, run_id, source_url, source_kind, source_id, track_id,
                  title, artist, album_title, album_artist, album_year,
                  track_number, cover_id, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    run_id,
                    source_url,
                    source_kind,
                    source_id,
                    track.get("track_id"),
                    track.get("title"),
                    track.get("artist"),
                    track.get("album_title"),
                    track.get("album_artist"),
                    track.get("album_year"),
                    track.get("track_number"),
                    track.get("cover_id"),
                    status,
                    now,
                    now,
                ),
            )
        return self.get_queue_item(item_id)

    def get_queue_item(self, item_id: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM queue_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_queue_item(self, item_id: str, **fields) -> dict | None:
        if not fields:
            return self.get_queue_item(item_id)
        allowed = {
            "status",
            "progress_current",
            "progress_total",
            "attempts",
            "error",
            "output_path",
            "track_id",
            "title",
            "artist",
            "album_title",
            "album_artist",
            "album_year",
            "track_number",
            "cover_id",
        }
        assignments = []
        values = []
        for key, value in fields.items():
            if key not in allowed:
                raise ValueError(f"Unsupported queue item field: {key}")
            assignments.append(f"{key} = ?")
            values.append(value)
        assignments.append("updated_at = ?")
        values.append(time.time())
        values.append(item_id)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE queue_items SET {', '.join(assignments)} WHERE id = ?",
                values,
            )
        return self.get_queue_item(item_id)

    def list_queue_items(self, run_id: str | None = None) -> list[dict]:
        query = "SELECT * FROM queue_items"
        values: tuple = ()
        if run_id is not None:
            query += " WHERE run_id = ?"
            values = (run_id,)
        query += " ORDER BY created_at, rowid"
        with self.connect() as connection:
            rows = connection.execute(query, values).fetchall()
        return [dict(row) for row in rows]

    def list_queue_items_by_status(self, run_id: str, statuses: set[str]) -> list[dict]:
        if not statuses:
            return []
        placeholders = ", ".join("?" for _ in statuses)
        values = [run_id, *sorted(statuses)]
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM queue_items
                WHERE run_id = ? AND status IN ({placeholders})
                ORDER BY created_at, rowid
                """,
                values,
            ).fetchall()
        return [dict(row) for row in rows]

    def retry_queue_item(self, item_id: str) -> dict | None:
        item = self.get_queue_item(item_id)
        if item is None:
            return None
        return self.update_queue_item(
            item_id,
            status="ready",
            attempts=int(item.get("attempts") or 0) + 1,
            error=None,
            progress_current=0,
            progress_total=0,
        )

    def cancel_queued_items(self, run_id: str) -> None:
        now = time.time()
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE queue_items
                SET status = 'cancelled', updated_at = ?
                WHERE run_id = ? AND status IN ('queued', 'ready', 'failed')
                """,
                (now, run_id),
            )

    def _run_from_row(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        data["options"] = json.loads(data.pop("options_json") or "{}")
        return data
