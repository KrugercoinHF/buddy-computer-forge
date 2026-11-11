import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS nodes (
      id TEXT PRIMARY KEY, name TEXT NOT NULL, hostname TEXT NOT NULL,
      token_hash TEXT NOT NULL, node_type TEXT NOT NULL, telemetry TEXT NOT NULL,
      last_seen TEXT, created_at TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'offline'
    );
    CREATE TABLE IF NOT EXISTS missions (
      id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
      status TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY, mission_id TEXT, task_type TEXT NOT NULL,
      payload TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
      approved INTEGER, submitted_code TEXT DEFAULT '', claimed_by TEXT,
      lease_until TEXT, stdout TEXT, stderr TEXT, exit_code INTEGER,
      FOREIGN KEY(mission_id) REFERENCES missions(id)
    );
    CREATE TABLE IF NOT EXISTS approvals (
      id TEXT PRIMARY KEY, task_id TEXT NOT NULL, decision TEXT NOT NULL,
      actor TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL,
      submitted_code TEXT NOT NULL,
      FOREIGN KEY(task_id) REFERENCES tasks(id)
    );
    CREATE TABLE IF NOT EXISTS audit_events (
      id TEXT PRIMARY KEY, event_type TEXT NOT NULL, node_id TEXT,
      task_id TEXT, message TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at);
    CREATE INDEX IF NOT EXISTS idx_approvals_task_created ON approvals(task_id, created_at);
    """
    with get_connection() as connection:
        connection.executescript(schema)


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    with get_connection() as connection:
        cursor = connection.execute(sql, tuple(params))
        return cursor.rowcount


def fetch_one(sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(sql, tuple(params)).fetchone()


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(sql, tuple(params)).fetchall()
