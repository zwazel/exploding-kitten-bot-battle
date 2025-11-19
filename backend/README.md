# Arena Backend

FastAPI service responsible for user accounts, bot uploads, replay management, and running arena matches.

## Installation

From the repository root:

```bash
pip install -e ./backend[dev]
```

Or from the `backend/` directory:

```bash
pip install -e .[dev]
```

## Environment Configuration

Configuration is managed via environment variables (prefix `ARENA_`) or a `.env` file. See `app/config.py`.

- `ARENA_DATABASE_URL`: SQLAlchemy URL (default: `postgresql+psycopg2://exploding:exploding@localhost:5432/exploding`).
- `ARENA_SECRET_KEY`: JWT signing secret (default: `change-me`).
- `ARENA_ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime (default: 120).
- `ARENA_ALLOWED_ORIGINS`: CORS origins (default: `http://localhost:5173,http://127.0.0.1:5173`).
- `ARENA_STORAGE_ROOT`: Path for uploads (default: `backend/storage`).
- `ARENA_BUILTIN_BOTS_DIRECTORY`: Path to reference bots (default: `bots`).

## Running Locally

### With Docker (Recommended)

```bash
docker compose up --build
```
Runs Postgres and Backend. API at http://localhost:8000.

### Manual Run

Ensure Postgres is running and `ARENA_DATABASE_URL` is set.

```bash
# From repository root
uvicorn app.main:app --app-dir backend/app --reload
```

## Database Migrations

Migrations are handled by Alembic and run automatically on startup.

```bash
cd backend
alembic upgrade head
```

## Admin Setup (Seeding Bots)

To seed the arena with reference bots:

```bash
python -m app.commands.setup_admin \
  --email admin@example.com \
  --display-name AdminUser \
  --password supersecret \
  --bots-dir ./bots
```
