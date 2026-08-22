from __future__ import annotations

from typing import Protocol

from movievoter.models.movie import MovieDetails, MovieSearchResult


class MovieProvider(Protocol):
    async def search(
        self,
        query: str,
        *,
        language: str = "ru-RU",
        limit: int = 8,
    ) -> list[MovieSearchResult]: ...

    async def get_details(
        self,
        external_id: str,
        *,
        language: str = "ru-RU",
    ) -> MovieDetails: ...
