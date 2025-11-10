# Arena Backend

FastAPI service responsible for user accounts, bot uploads, replay management, and running arena matches.

## Installation

```bash
pip install -e ./backend[dev]
```

This installs the API together with pytest and httpx for tests.

## Environment

Configuration keys (prefix `ARENA_`) are defined in `app/config.py`:

- `ARENA_DATABASE_URL` – SQLAlchemy URL (default points to `postgresql+psycopg2://exploding:exploding@localhost:5432/exploding`).
- `ARENA_SECRET_KEY` – JWT signing secret (default `change-me`).
- `ARENA_ACCESS_TOKEN_EXPIRE_MINUTES` – token lifetime (default 120 minutes).
- `ARENA_ALLOWED_ORIGINS` – comma-separated list of origins for CORS (defaults to `http://localhost:5173,http://127.0.0.1:5173`).
- `ARENA_STORAGE_ROOT` – path for uploaded bots and replay JSON files (`backend/storage`).

## Running locally

```bash
uvicorn app.main:app --app-dir backend/app --reload
```

The OpenAPI docs are available at <http://localhost:8000/docs>.

## Tests

```bash
pytest backend/app/tests
```

Tests use an isolated SQLite database and exercise the sign-up/login flow plus bot upload + replay retrieval.

## Match execution overview

1. On upload the backend saves the bot file under `storage/bots/user_<id>/version_<n>.py`.
2. The bot is validated by importing it and ensuring it subclasses `game.Bot`.
3. A match is executed with the uploaded bot and four opponents (other active bots or built-ins from `bots/`).
4. A replay JSON file is written to `storage/replays/` and database records (bot versions, replay participants) are persisted.
5. Prior bot files are removed from disk but their metadata remains to preserve replay history.
