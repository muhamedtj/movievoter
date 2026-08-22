from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT NOT NULL,
    language TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY,
    title TEXT,
    language TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_members (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, user_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    external_provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    original_title TEXT,
    year INTEGER,
    director TEXT,
    poster_url TEXT,
    runtime_minutes INTEGER,
    genres_json TEXT NOT NULL DEFAULT '[]',
    overview TEXT,
    trailer_url TEXT,
    suggested_by INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'waiting'
        CHECK (status IN ('waiting', 'voting', 'watching', 'done')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (chat_id, external_provider, external_id),
    UNIQUE (chat_id, id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id, suggested_by)
        REFERENCES chat_members(chat_id, user_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_movies_chat_status
    ON movies(chat_id, status);

CREATE TABLE IF NOT EXISTS interest_ratings (
    chat_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, movie_id, user_id),
    FOREIGN KEY (chat_id, movie_id)
        REFERENCES movies(chat_id, id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id, user_id)
        REFERENCES chat_members(chat_id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interest_ratings_movie
    ON interest_ratings(chat_id, movie_id);

CREATE TABLE IF NOT EXISTS vote_settings (
    chat_id INTEGER PRIMARY KEY,
    duration_seconds INTEGER NOT NULL DEFAULT 86400,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vote_requests (
    chat_id INTEGER PRIMARY KEY,
    requested_by INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deadline_at TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id, requested_by)
        REFERENCES chat_members(chat_id, user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vote_sessions (
    chat_id INTEGER PRIMARY KEY,
    poll_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    options_json TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deadline_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'finishing', 'finished', 'cancelled')),
    UNIQUE (chat_id, poll_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS poll_votes (
    chat_id INTEGER NOT NULL,
    poll_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    option_index INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, poll_id, user_id),
    FOREIGN KEY (chat_id, poll_id)
        REFERENCES vote_sessions(chat_id, poll_id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id, user_id)
        REFERENCES chat_members(chat_id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_poll_votes_session
    ON poll_votes(chat_id, poll_id);

CREATE TABLE IF NOT EXISTS rating_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'closed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT,
    UNIQUE (chat_id, movie_id),
    UNIQUE (chat_id, id),
    FOREIGN KEY (chat_id, movie_id)
        REFERENCES movies(chat_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rating_round_members (
    chat_id INTEGER NOT NULL,
    round_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (chat_id, round_id, user_id),
    FOREIGN KEY (chat_id, round_id)
        REFERENCES rating_rounds(chat_id, id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id, user_id)
        REFERENCES chat_members(chat_id, user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS final_ratings (
    chat_id INTEGER NOT NULL,
    round_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    score INTEGER CHECK (score BETWEEN 1 AND 10),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, round_id, user_id),
    FOREIGN KEY (chat_id, round_id)
        REFERENCES rating_rounds(chat_id, id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id, round_id, user_id)
        REFERENCES rating_round_members(chat_id, round_id, user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hall_of_fame (
    chat_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    final_club_rating REAL NOT NULL,
    weighted_rating REAL NOT NULL,
    votes_count INTEGER NOT NULL,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, movie_id),
    FOREIGN KEY (chat_id, movie_id)
        REFERENCES movies(chat_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stage_messages (
    chat_id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('voting', 'winner', 'final_rating', 'final')),
    pinned INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pin_service_messages (
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, message_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ui_messages (
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    PRIMARY KEY (chat_id, message_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS error_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id INTEGER,
    source_screen TEXT,
    description TEXT,
    attachment_type TEXT,
    attachment_file_id TEXT,
    build_sha TEXT,
    deployment_id TEXT,
    service_name TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'FIXED', 'CLOSED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(tg_id) ON DELETE RESTRICT,
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE SET NULL
);
"""


class Database:
    """Small aiosqlite adapter used by repositories.

    The import is intentionally lazy so pure business-rule tests can run without
    importing Telegram or database dependencies.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._connection: Any | None = None
        self._transaction_lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._connection is not None:
            return
        try:
            import aiosqlite
        except ImportError as exc:  # pragma: no cover - environment failure
            raise RuntimeError("aiosqlite is required to run MovieVoter") from exc

        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.execute("PRAGMA busy_timeout = 5000")
        await self._connection.execute("PRAGMA journal_mode = WAL")
        await self._connection.commit()

    async def close(self) -> None:
        if self._connection is None:
            return
        await self._connection.close()
        self._connection = None

    async def initialize(self) -> None:
        conn = self._require_connection()
        await conn.executescript(SCHEMA_SQL)
        await conn.commit()

    async def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> int:
        conn = self._require_connection()
        cursor = await conn.execute(sql, parameters)
        await conn.commit()
        return cursor.lastrowid

    async def fetchone(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        conn = self._require_connection()
        cursor = await conn.execute(sql, parameters)
        return await cursor.fetchone()

    async def fetchall(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        conn = self._require_connection()
        cursor = await conn.execute(sql, parameters)
        return list(await cursor.fetchall())

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[Any]:
        conn = self._require_connection()
        async with self._transaction_lock:
            await conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except Exception:
                await conn.rollback()
                raise
            else:
                await conn.commit()

    def _require_connection(self) -> Any:
        if self._connection is None:
            raise RuntimeError("Database.connect() must be called first")
        return self._connection
