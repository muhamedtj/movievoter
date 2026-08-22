from __future__ import annotations

from movievoter.database import Database
from movievoter.models.movie import MovieCandidate
from movievoter.repositories.movies import TenantViolationError


class InterestRatingsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(
        self,
        chat_id: int,
        movie_id: int,
        user_id: int,
        score: int,
    ) -> None:
        if not 1 <= score <= 10:
            raise ValueError("Interest score must be between 1 and 10")

        movie = await self.db.fetchone(
            "SELECT status FROM movies WHERE chat_id = ? AND id = ?",
            (chat_id, movie_id),
        )
        if movie is None:
            raise TenantViolationError("Movie does not belong to this club")
        if movie["status"] != "waiting":
            raise ValueError("Interest can only be rated for waiting movies")

        member = await self.db.fetchone(
            "SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        if member is None:
            raise TenantViolationError("User is not a member of this club")

        await self.db.execute(
            """
            INSERT INTO interest_ratings(chat_id, movie_id, user_id, score)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, movie_id, user_id) DO UPDATE SET
                score = excluded.score,
                updated_at = CURRENT_TIMESTAMP
            """,
            (chat_id, movie_id, user_id, score),
        )

    async def eligible_candidates(
        self,
        chat_id: int,
        required_ratings: int,
        limit: int = 10,
    ) -> list[MovieCandidate]:
        rows = await self.db.fetchall(
            """
            SELECT
                m.id AS movie_id,
                m.title,
                m.year,
                AVG(ir.score) AS average_score,
                COUNT(ir.score) AS rating_count
            FROM movies AS m
            JOIN interest_ratings AS ir
              ON ir.chat_id = m.chat_id AND ir.movie_id = m.id
            WHERE m.chat_id = ? AND m.status = 'waiting'
            GROUP BY m.chat_id, m.id
            HAVING COUNT(ir.score) >= ?
            ORDER BY average_score DESC, rating_count DESC, m.id ASC
            LIMIT ?
            """,
            (chat_id, required_ratings, limit),
        )
        return [
            MovieCandidate(
                movie_id=int(row["movie_id"]),
                title=str(row["title"]),
                year=int(row["year"]) if row["year"] is not None else None,
                average_score=float(row["average_score"]),
                rating_count=int(row["rating_count"]),
            )
            for row in rows
        ]
