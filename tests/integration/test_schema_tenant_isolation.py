import sqlite3

import pytest

from movievoter.database import SCHEMA_SQL


def setup_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    return conn


def add_chat_member(
    conn: sqlite3.Connection,
    chat_id: int,
    user_id: int,
    name: str,
) -> None:
    conn.execute(
        "INSERT INTO chats(chat_id, title) VALUES (?, ?)",
        (chat_id, f"Club {chat_id}"),
    )
    conn.execute(
        "INSERT INTO users(tg_id, full_name) VALUES (?, ?)",
        (user_id, name),
    )
    conn.execute(
        "INSERT INTO chat_members(chat_id, user_id) VALUES (?, ?)",
        (chat_id, user_id),
    )


def test_cross_tenant_interest_rating_is_rejected_by_database() -> None:
    conn = setup_db()
    add_chat_member(conn, -1001, 1, "Alice")
    add_chat_member(conn, -1002, 2, "Bob")

    movie_id = conn.execute(
        """
        INSERT INTO movies(chat_id, external_provider, external_id, title, suggested_by)
        VALUES (-1001, 'tmdb', '157336', 'Interstellar', 1)
        """
    ).lastrowid

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO interest_ratings(chat_id, movie_id, user_id, score)
            VALUES (?, ?, ?, ?)
            """,
            (-1002, movie_id, 2, 10),
        )


def test_non_member_cannot_be_suggestor() -> None:
    conn = setup_db()
    add_chat_member(conn, -1001, 1, "Alice")
    conn.execute("INSERT INTO users(tg_id, full_name) VALUES (2, 'Outsider')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO movies(chat_id, external_provider, external_id, title, suggested_by)
            VALUES (-1001, 'tmdb', '1', 'Movie', 2)
            """
        )


def test_same_external_movie_can_exist_in_different_clubs() -> None:
    conn = setup_db()
    add_chat_member(conn, -1001, 1, "Alice")
    add_chat_member(conn, -1002, 2, "Bob")

    conn.execute(
        """
        INSERT INTO movies(chat_id, external_provider, external_id, title, suggested_by)
        VALUES (-1001, 'tmdb', '157336', 'Interstellar', 1)
        """
    )
    conn.execute(
        """
        INSERT INTO movies(chat_id, external_provider, external_id, title, suggested_by)
        VALUES (-1002, 'tmdb', '157336', 'Interstellar', 2)
        """
    )

    assert conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0] == 2
