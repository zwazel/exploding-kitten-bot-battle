# Exploding Kitten Bot Battle

A complete toolkit for building, testing, and battling Exploding Kitten bots.

## Repository Layout

- `game/` & `bots/`: Core Python game engine and reference bots.
- `backend/`: FastAPI service for arena matches, user accounts, and replay storage.
- `frontend/`: Vite + TypeScript web app (replay viewer + arena dashboard).
- `main.py`: CLI entry point for local simulations.
- `tests/`: Unit tests for the game engine.

## Prerequisites

- Python 3.10+
- Node.js 20+
- Docker (optional, for full stack)

## 1. Local Simulation (No Backend)

Iterate on bots locally without the full arena stack:

```bash
# Run engine tests
python -m unittest tests.test_game -v

# Run a match and generate a replay
python main.py --replay my-local-replay.json
```

Upload the resulting JSON to the "Replay Viewer" in the frontend (or use the hosted version) to watch the match.

## 2. Backend Setup

The backend manages the arena, user accounts, and hosted matches.

```bash
cd backend
pip install -e .[dev]
pytest app/tests
```

### Running with Docker (Recommended)

```bash
docker compose up --build
```
Starts Postgres and the backend at http://localhost:8000. Docs at `/docs`.

### Running Manually

```bash
export ARENA_DATABASE_URL="postgresql+psycopg2://exploding:exploding@localhost:5432/exploding"
uvicorn app.main:app --app-dir backend/app --reload
```

See `backend/README.md` for more details on configuration and migrations.

## 3. Frontend Setup

The frontend provides the UI for the arena and replay viewer.

```bash
cd frontend
npm install
npm run dev
```
Access at http://localhost:5173.

See `frontend/README.md` for testing and build instructions.

## Bot Development & Cheat Prevention

When writing bots, you will interact with the game state and other players. To ensure fairness, the game uses a `BotProxy` system.

### Key Rules
1.  **No Direct Hand Access**: You cannot see the cards in an opponent's hand. `opponent.hand` will return a list of `None` or be inaccessible for card details.
2.  **Use Public Info**: You CAN access:
    - `opponent.name`
    - `opponent.alive`
    - `len(opponent.hand)`
3.  **Do Not Modify State**: You cannot modify the `GameState` or other bots.

### Example: Choosing a Target

```python
def choose_target(self, state, alive_players, context):
    # ✅ GOOD: Target player with most cards
    return max(alive_players, key=lambda b: len(b.hand))

    # ❌ BAD: Trying to find a player with a specific card
    # for p in alive_players:
    #     if CardType.DEFUSE in p.hand: ... # Will fail or return False
```

## Contributing

- **Backend**: Add tests in `backend/app/tests/`.
- **Frontend**: Ensure the offline Replay Viewer continues to work.
- **Bots**: Add new reference bots to `bots/` and run the admin setup script to seed them.
