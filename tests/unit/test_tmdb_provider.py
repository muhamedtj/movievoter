import httpx
import pytest

from movievoter.providers.tmdb import TMDBProvider


@pytest.mark.asyncio
async def test_tmdb_search_maps_year_and_poster() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/3/search/movie"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 157336,
                        "title": "Интерстеллар",
                        "original_title": "Interstellar",
                        "release_date": "2014-11-05",
                        "poster_path": "/poster.jpg",
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = TMDBProvider("token", client=client)
    results = await provider.search("Интерстеллар")
    await client.aclose()

    assert len(results) == 1
    assert results[0].external_id == "157336"
    assert results[0].year == 2014
    assert results[0].poster_url == "https://image.tmdb.org/t/p/w500/poster.jpg"


@pytest.mark.asyncio
async def test_tmdb_details_extracts_director_and_trailer() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 157336,
                "title": "Интерстеллар",
                "original_title": "Interstellar",
                "release_date": "2014-11-05",
                "poster_path": "/poster.jpg",
                "runtime": 169,
                "genres": [{"name": "Science Fiction"}],
                "overview": "A space epic.",
                "credits": {"crew": [{"job": "Director", "name": "Christopher Nolan"}]},
                "videos": {
                    "results": [
                        {
                            "site": "YouTube",
                            "type": "Trailer",
                            "official": True,
                            "key": "abc123",
                        }
                    ]
                },
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = TMDBProvider("token", client=client)
    movie = await provider.get_details("157336")
    await client.aclose()

    assert movie.director == "Christopher Nolan"
    assert movie.runtime_minutes == 169
    assert movie.genres == ("Science Fiction",)
    assert movie.trailer_url == "https://www.youtube.com/watch?v=abc123"
