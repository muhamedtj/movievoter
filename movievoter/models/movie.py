from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MovieSearchResult:
    external_id: str
    title: str
    original_title: str | None
    year: int | None
    poster_url: str | None = None


@dataclass(frozen=True, slots=True)
class MovieDetails:
    external_provider: str
    external_id: str
    title: str
    original_title: str | None
    year: int | None
    director: str | None
    poster_url: str | None
    runtime_minutes: int | None
    genres: tuple[str, ...]
    overview: str | None
    trailer_url: str | None


@dataclass(frozen=True, slots=True)
class MovieCandidate:
    movie_id: int
    title: str
    year: int | None
    average_score: float
    rating_count: int
