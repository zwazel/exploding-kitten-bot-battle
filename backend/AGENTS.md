# Backend Agent Guidelines

- All backend code lives under `backend/app`. Use Python typing annotations and prefer dependency-injected database sessions.
- Tests should be written with `pytest` in `backend/app/tests/` and may rely on an in-memory SQLite database for speed.
- Whenever you add a new API route, update the OpenAPI-serving FastAPI app and the backend README if usage changes.
- Secrets such as JWT keys must be configurable through environment variables (see `config.py`).
