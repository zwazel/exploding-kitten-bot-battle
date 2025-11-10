# Agent Guidelines

This repository now contains three major components:

- `game/` and `bots/`: the reusable simulation engine and built-in bots.
- `backend/`: the FastAPI arena API.
- `frontend/`: the Vite/TypeScript single page application.

General expectations for future changes:

- Prefer adding automated tests for backend Python changes under `backend/app/tests/` (pytest) and keep existing unit tests for the game engine passing.
- Keep the ability to run everything locally via the documented commands in `README.md`.
- When modifying documentation, ensure references stay aligned between the backend and frontend guides.
- Avoid committing build artifacts (e.g., `dist/`, `coverage/`, `__pycache__`).

Component-specific conventions are documented in nested `AGENTS.md` files.
