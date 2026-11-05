"""Durable local event queue (SQLite). Events survive restarts and internet outages."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path


class EventQueue:
    def __init__(self, path: Path | str, max_events: int = 100_000) -> None:
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, "
            "payload TEXT NOT NULL, attempts INTEGER DEFAULT 0)"
        )
        self._lock = threading.Lock()
        self.max_events = max_events
        self.dropped = 0

    def push(self, event: dict) -> str:
        key = event.get("idempotency_key") or uuid.uuid4().hex
        event = {**event, "idempotency_key": key}
        with self._lock:
            self._conn.execute("INSERT OR IGNORE INTO events (key, payload) VALUES (?, ?)", (key, json.dumps(event)))
            n = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            if n > self.max_events:  # bounded disk use: drop oldest and count it (reported in heartbeat)
                over = n - self.max_events
                self._conn.execute("DELETE FROM events WHERE seq IN (SELECT seq FROM events ORDER BY seq LIMIT ?)", (over,))
                self.dropped += over
        return key

    def peek(self, limit: int = 200) -> list[tuple[int, dict]]:
        with self._lock:
            rows = self._conn.execute("SELECT seq, payload FROM events ORDER BY seq LIMIT ?", (limit,)).fetchall()
        return [(seq, json.loads(p)) for seq, p in rows]

    def ack(self, seqs: list[int]) -> None:
        if not seqs:
            return
        with self._lock:
            self._conn.executemany("DELETE FROM events WHERE seq = ?", [(s,) for s in seqs])

    def mark_attempt(self, seqs: list[int]) -> None:
        with self._lock:
            self._conn.executemany("UPDATE events SET attempts = attempts + 1 WHERE seq = ?", [(s,) for s in seqs])

    def depth(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def close(self) -> None:
        self._conn.close()
