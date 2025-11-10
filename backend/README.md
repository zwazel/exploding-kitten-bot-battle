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

## Database Migrations

The backend uses Alembic for database schema migrations. Migrations are automatically applied on application startup, but you can also run them manually.

### Automatic migrations

When the backend starts, it automatically runs all pending migrations. This ensures the database schema is always up to date.

### Manual migration management

```bash
# Check current migration status
cd backend
alembic current

# View migration history
alembic history

# Manually run migrations (if needed)
alembic upgrade head

# Downgrade to a specific revision (use with caution)
alembic downgrade <revision>

# Create a new migration after model changes
alembic revision --autogenerate -m "description_of_changes"
```

### Troubleshooting database issues

If you encounter errors like "column does not exist" or other schema mismatches:

1. **With Docker:** Reset the database by removing volumes:
   ```bash
   docker compose down -v  # Remove volumes
   docker compose up --build  # Recreate with fresh database
   ```

2. **Without Docker:** Drop and recreate the database, then run migrations:
   ```bash
   # Using psql
   dropdb exploding
   createdb exploding
   cd backend
   alembic upgrade head
   ```

3. **Check migration status:**
   ```bash
   cd backend
   alembic current  # Shows current revision
   alembic history  # Shows all migrations
   ```

## Tests

```bash
pytest backend/app/tests
```

Tests use an isolated SQLite database and exercise the sign-up/login flow plus multi-bot management, arena uploads, and replay retrieval.

## Admin bot seeding

The arena no longer ships with hard-coded opponents. Instead, seed the initial roster by importing the bots in the repository’s `bots/` directory (or any directory containing compatible `.py` files) into a dedicated admin account. Run the setup command any time you add or update reference bots:

```bash
python -m app.commands.setup_admin \
  --email admin@example.com \
  --display-name AdminUser \
  --password supersecret \
  --bots-dir ./bots
```

The script is idempotent: it creates/updates the admin user, uploads each bot, and only creates a new version when the file hash changes. Bot files are copied into the storage directory, so you can keep the source files in version control while the arena uses its own copies.

## Match execution overview

1. On upload the backend saves the bot file under `storage/bots/user_<user_id>/bot_<bot_id>/version_<n>.py`.
2. The bot is validated by importing it and ensuring it subclasses `game.Bot`.
3. A match is executed with the uploaded bot and a random sample of other active bots (including the admin-seeded roster). If fewer than two participants are available, the backend responds with `409 Conflict`.
4. A replay JSON file is written to `storage/replays/` and database records (bot versions, replay participants) are persisted.
5. Prior bot files are removed from disk but their metadata (version numbers, replay links) remains to preserve history.

### Bot naming rules

- Usernames are normalised to lowercase alphanumeric identifiers automatically during sign-up. The global arena label for a bot is `username_botname`.
- Bot names must only contain letters, numbers, underscores, or hyphens. Each user can own multiple bots, but bot names must be unique per user. The combination of username + bot name is globally unique.
- Deleting a bot removes its active version from the filesystem while preserving replays with historical metadata.
