# Exploding Kitten Bot Battle

A complete toolkit for building, testing, and battling Exploding Kitten bots. The repository now contains three cooperating parts:

1. **Game engine (`game/`, `bots/`, `main.py`)** – the Python implementation of Exploding Kittens used for local simulation.
2. **Arena backend (`backend/`)** – a FastAPI service that accepts bot uploads, runs arena matches, stores replays, and exposes history over a PostgreSQL database.
3. **Arena frontend (`frontend/`)** – a Vite + TypeScript single page app that combines the original replay viewer with arena account and bot management.

The existing replay viewer behaviour is preserved: you can still load local replay files without signing in. When authenticated, the same UI lets you upload bots to the arena and review hosted replays.

## Repository layout

```
exploding-kitten-bot-battle/
├── backend/              # FastAPI backend service, commands, and tests
├── bots/                 # Reference bots (synced to the arena via the admin script)
├── docker-compose.yml    # Local orchestration for Postgres + backend
├── frontend/             # Vite web application (viewer + arena dashboard)
├── game/                 # Core game engine
├── main.py               # CLI entry point for local simulations
├── tests/                # Original unit tests for the game engine
└── ...                   # Docs, screenshots, etc.
```

## Prerequisites

- Python 3.10+
- Node.js 20+
- Docker (optional, for running the full stack locally)

## 1. Run local simulations

The original workflow for iterating on bots still works.

```bash
python -m unittest tests.test_game -v              # verify engine integrity
python main.py --replay my-local-replay.json        # run a match and record a replay
```

Drop the resulting JSON file into the “Replay Viewer” tab of the frontend to inspect it – no login required.

## 2. Backend setup

### Install dependencies & run tests

```bash
pip install -e ./backend[dev]
pytest backend/app/tests
```

### Run with a local Postgres instance

The backend expects a PostgreSQL database. You can provide one manually through the `ARENA_DATABASE_URL` environment variable, or use the included Compose file:

```bash
docker compose up --build
```

This starts Postgres (credentials `exploding/exploding`) and the backend on <http://localhost:8000>. The backend exposes OpenAPI docs at `/docs`.

To run without Docker, point to your database and launch uvicorn:

```bash
export ARENA_DATABASE_URL="postgresql+psycopg2://exploding:exploding@localhost:5432/exploding"
uvicorn app.main:app --app-dir backend/app --reload
```

Backend configuration is documented in `backend/app/config.py` – environment variables are prefixed with `ARENA_` (e.g., `ARENA_SECRET_KEY`, `ARENA_ALLOWED_ORIGINS`). Uploaded bot files and arena replays are stored under `backend/storage/` (mounted as a volume in Compose).

#### Seed arena bots

After the backend is running, create an admin account and sync the reference bots so that every match has opponents available. The command is idempotent and can be re-run whenever files in `bots/` change:

```bash
python -m app.commands.setup_admin \
  --email admin@example.com \
  --display-name AdminUser \
  --password supersecret \
  --bots-dir ./bots
```

The script computes a hash for each bot file; unchanged bots keep their existing version numbers, while updated files create a new version automatically.

## 3. Frontend setup

The frontend lives under `frontend/` and now combines:

- The local replay viewer from the original project.
- An arena dashboard with login/signup, bot upload, version history, and replay browsing.

```bash
cd frontend
npm install
npm run dev   # served on http://localhost:5173
npm test      # Playwright UI tests
```

The app reads the backend origin from `VITE_API_BASE_URL` (defaults to `http://localhost:8000`). Deployments to GitHub Pages continue to work via `.github/workflows/deploy-pages.yml`.

## Arena workflow overview

1. Seed the arena with the reference bots using the admin setup script (see above) so there are opponents available.
2. Sign up and log in through the “Arena” tab. Usernames are normalised to lowercase identifiers and combined with bot names to form global labels (`username_botname`).
3. Create one or more bots from the dashboard, then upload Python files (`.py`) for each bot. The backend validates the class and stores a new version when the file hash changes.
4. Every upload runs an arena match against a random set of up to four other active bots. The replay, placements, and bot version history become available in the dashboard and any replay can be downloaded or opened in the viewer tab.

## Additional tooling

- **Backend container** – `backend/Dockerfile` builds a production-ready image using uvicorn.
- **Automated tests** – CI runs unit tests for the game engine, pytest-based backend tests, and Playwright UI tests for the frontend.
- **Storage layout** – arena uploads and generated replays live under `backend/storage/bots/` and `backend/storage/replays/` so they can be mounted or backed up separately.

## Contributing

See `CONTRIBUTING.md` for general guidelines. When touching backend code, add pytest coverage under `backend/app/tests/`; when touching the frontend, keep the replay viewer’s offline workflow intact.
