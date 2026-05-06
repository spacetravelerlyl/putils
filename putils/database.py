from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ConfigStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (namespace, key)
                )
                """
            )

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def set(self, namespace: str, key: str, value: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO settings(namespace, key, value, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (namespace, key, json.dumps(value), utc_now_iso()),
            )


class LogStore:
    def __init__(self, db_path: Path, retention_limit: int | None = None) -> None:
        self.db_path = db_path
        self.retention_limit = retention_limit
        self._init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    plugin_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at
                ON operation_logs(created_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_operation_logs_id
                ON operation_logs(id)
                """
            )

    def set_retention_limit(self, retention_limit: int | None) -> None:
        self.retention_limit = retention_limit

    def rotate(self, retention_limit: int | None = None) -> int:
        limit = self.retention_limit if retention_limit is None else retention_limit
        if limit is None or limit < 1:
            return 0
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id FROM operation_logs
                ORDER BY id DESC
                LIMIT 1 OFFSET ?
                """,
                (limit - 1,),
            ).fetchone()
            if row is None:
                return 0
            cursor = conn.execute("DELETE FROM operation_logs WHERE id < ?", (row["id"],))
            return cursor.rowcount

    def add(self, plugin_id: str, level: str, message: str, details: dict[str, Any] | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO operation_logs(created_at, plugin_id, level, message, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    utc_now_iso(),
                    plugin_id,
                    level.upper(),
                    message,
                    json.dumps(details, ensure_ascii=False) if details else None,
                ),
            )
        self.rotate()

    def recent(self, limit: int = 200) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT id, created_at, plugin_id, level, message, details
                    FROM operation_logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )
