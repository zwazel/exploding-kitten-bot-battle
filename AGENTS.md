# Agent Guidelines

This repository contains the Exploding Kitten Bot Battle project, consisting of a Python game engine, a FastAPI backend, and a Vite+TypeScript frontend.

## Project Structure

- `game/` and `bots/`: Core game engine and reference bots.
- `backend/`: FastAPI arena backend (`backend/app`).
- `frontend/`: Vite+TypeScript single page application.
- `tests/`: Unit tests for the game engine.

## General Guidelines

- **Tests**: Prefer adding automated tests.
  - Backend: `backend/app/tests/` (pytest).
  - Frontend: `frontend/tests/` (Playwright).
  - Game Engine: `tests/` (unittest).
- **Local Execution**: Ensure all changes allow the project to be run locally as documented in `README.md`.
- **Documentation**: Keep `README.md` and other docs updated when changing features. Ensure backend and frontend docs stay aligned.
- **Artifacts**: Do not commit build artifacts (`dist/`, `coverage/`, `__pycache__`, etc.).

## Backend Guidelines (`backend/`)

- **Framework**: FastAPI with Pydantic models.
- **Database**: PostgreSQL with SQLAlchemy (async) and Alembic for migrations.
- **Testing**: Use `pytest`. Tests can use an in-memory SQLite database for speed.
- **Configuration**: All secrets and config must be handled via environment variables (see `backend/app/config.py`).
- **API**: Update OpenAPI documentation (auto-generated) and `backend/README.md` when adding/changing routes.

## Frontend Guidelines (`frontend/`)

- **Framework**: Vite + TypeScript.
- **State**: Minimal state management, prefer simple React/local state or lightweight stores if needed.
- **API**: Route all API requests through helpers in `src/api/`.
- **Responsiveness**: UI must work on screens down to 360px wide.
- **Local Replay**: The "Local Replay" feature must work without a backend connection.

## Bot Development (AI Context)

If asked to write a bot:
- Bots must inherit from `game.Bot`.
- Respect `BotProxy` limitations (cannot access opponent hands directly).
- Use `len(bot.hand)` for decision making regarding opponents.
