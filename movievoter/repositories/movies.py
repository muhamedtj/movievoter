from __future__ import annotations

import json

from movievoter.database import Database
from movievoter.models.movie import MovieDetails


class TenantViolationError(PermissionError):
    pass


class DuplicateMovieError(ValueError):
    pass


class MoviesRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def add_waiting_movie(
        self,
        chat_id: int,
        suggested_by: int,
        movie: MovieDetails,
    ) -> int:
        member = await self.db.fetchone(
            "SELECT 1 FROM chat_members WHERE chat_id = ? AND user_id = ?",
            (chat_id, suggested_by),
        )
        if member is None:
            raise TenantViolationError("Suggestor is not a member of this club")

        try:
            return await self.db.execute(
                """
                INSERT INTO movies(
                    chat_id, external_provider, external_id, title, original_title,
                    year, director, poster_url, runtime_minutes, genres_json,
                    overview, trailer_url, suggested_by, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting')
                """,
                (
                    chat_id,
                    movie.external_provider,
                    movie.external_id,
                    movie.title,
                    movie.original_title,
                    movie.year,
                    movie.director,
                    movie.poster_url,
                    movie.runtime_minutes,
                    json.dumps(movie.genres, ensure_ascii=False),
                    movie.overview,
                    movie.trailer_url,
                    suggested_by,
                ),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise DuplicateMovieError("Movie is already in this club") from exc
            raise

    async def get_for_chat(self, chat_id: int, movie_id: int):
        return await self.db.fetchone(
            "SELECT * FROM movies WHERE chat_id = ? AND id = ?",
            (chat_id, movie_id),
        )

    async def list_waiting(self, chat_id: int):
        return await self.db.fetchall(
            """
            SELECT * FROM movies
            WHERE chat_id = ? AND status = 'waiting'
            ORDER BY created_at, id
            """,
            (chat_id,),
        )
