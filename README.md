# MovieVoter

MovieVoter is a separate, multi-tenant Telegram bot for movie clubs. It is inspired by the working BookVoter product flow but uses a modular architecture instead of a large core plus runtime monkey patches.

## Product lifecycle

`Suggestion -> interest 1-10 -> quorum -> candidate selection -> poll -> winner -> watching -> final rating -> Hall of Fame -> statistics`

MovieVoter is designed to coexist with BookVoter in the same Telegram group. Its public commands are namespaced:

- `/movies`
- `/movieadmin`
- `/movietimer`

Generic `/admin`, `/suggest`, and `/votetimer` are intentionally not part of MovieVoter.

## Foundation architecture

```text
movievoter/
├── models/
├── repositories/
├── services/
├── providers/
├── routers/
├── keyboards/
└── middlewares/
```

Business rules belong in `services/`; persistence and tenant scoping belong in `repositories/`; external movie APIs belong in `providers/`; Telegram handlers stay thin.

## Database invariants

SQLite remains suitable for the first single-process deployment. The runtime adapter uses `aiosqlite`, enables foreign keys, WAL and a busy timeout.

Tenant isolation is enforced not only in SELECT queries but also in the schema: tenant-owned child rows use composite foreign keys containing `chat_id`. A rating from Club B cannot reference a movie from Club A even if a caller passes the wrong movie ID.

Core lifecycle tables are already reserved for voting, persistent poll votes, final-rating round membership snapshots, Hall of Fame, stage pins, transient UI cleanup and error reports with build/deployment metadata.

## Movie metadata provider

The first provider is TMDB behind a `MovieProvider` interface. Search is lightweight; selected movies are enriched with details, director credits and trailer metadata before persistence.

TMDB credentials are configured with `TMDB_READ_TOKEN`. Before production/commercial use, comply with TMDB attribution and licensing requirements.

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[test]"
pytest
```

Copy `.env.example` to `.env` before running the bot runtime in later phases.
