from __future__ import annotations

from datetime import date

import httpx

from movievoter.models.movie import MovieDetails, MovieSearchResult


class MovieProviderError(RuntimeError):
    pass


class TMDBProvider:
    provider_name = "tmdb"
    api_base_url = "https://api.themoviedb.org/3"
    poster_base_url = "https://image.tmdb.org/t/p/w500"

    def __init__(self, read_token: str, *, client: httpx.AsyncClient | None = None) -> None:
        if not read_token.strip():
            raise ValueError("TMDB read token is required")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15.0)
        self._headers = {
            "Authorization": f"Bearer {read_token.strip()}",
            "Accept": "application/json",
        }

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def search(
        self,
        query: str,
        *,
        language: str = "ru-RU",
        limit: int = 8,
    ) -> list[MovieSearchResult]:
        normalized = query.strip()
        if not normalized:
            return []
        payload = await self._get(
            "/search/movie",
            params={"query": normalized, "language": language, "include_adult": "false"},
        )
        results = payload.get("results", [])[: max(1, min(limit, 20))]
        return [
            MovieSearchResult(
                external_id=str(item["id"]),
                title=item.get("title") or item.get("original_title") or "Untitled",
                original_title=item.get("original_title"),
                year=self._year(item.get("release_date")),
                poster_url=self._poster(item.get("poster_path")),
            )
            for item in results
            if item.get("id") is not None
        ]

    async def get_details(self, external_id: str, *, language: str = "ru-RU") -> MovieDetails:
        payload = await self._get(
            f"/movie/{external_id}",
            params={"language": language, "append_to_response": "credits,videos"},
        )
        director = next(
            (
                person.get("name")
                for person in payload.get("credits", {}).get("crew", [])
                if person.get("job") == "Director"
            ),
            None,
        )
        videos = payload.get("videos", {}).get("results", [])
        trailer = next(
            (
                item
                for item in videos
                if item.get("site") == "YouTube"
                and item.get("type") == "Trailer"
                and item.get("official")
            ),
            None,
        ) or next(
            (
                item
                for item in videos
                if item.get("site") == "YouTube" and item.get("type") == "Trailer"
            ),
            None,
        )
        trailer_url = (
            f"https://www.youtube.com/watch?v={trailer['key']}"
            if trailer and trailer.get("key")
            else None
        )

        return MovieDetails(
            external_provider=self.provider_name,
            external_id=str(payload["id"]),
            title=payload.get("title") or payload.get("original_title") or "Untitled",
            original_title=payload.get("original_title"),
            year=self._year(payload.get("release_date")),
            director=director,
            poster_url=self._poster(payload.get("poster_path")),
            runtime_minutes=payload.get("runtime"),
            genres=tuple(
                genre["name"]
                for genre in payload.get("genres", [])
                if genre.get("name")
            ),
            overview=payload.get("overview") or None,
            trailer_url=trailer_url,
        )

    async def _get(self, path: str, *, params: dict[str, str]) -> dict:
        try:
            response = await self._client.get(
                f"{self.api_base_url}{path}",
                headers=self._headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MovieProviderError(f"TMDB request failed: {exc}") from exc

    @classmethod
    def _poster(cls, poster_path: str | None) -> str | None:
        return f"{cls.poster_base_url}{poster_path}" if poster_path else None

    @staticmethod
    def _year(raw: str | None) -> int | None:
        if not raw:
            return None
        try:
            return date.fromisoformat(raw).year
        except ValueError:
            return None
