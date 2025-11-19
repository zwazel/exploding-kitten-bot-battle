# Arena Frontend

Vite + TypeScript application for the Exploding Kitten Bot Battle.

## Features

- **Replay Viewer**: Watch matches by dropping in a JSON replay file (offline capable).
- **Arena Dashboard**: Manage bots, view history, and trigger matches (requires backend).
- **Responsive**: Works on mobile and desktop.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Access at http://localhost:5173.

## Configuration

- `VITE_API_BASE_URL`: URL of the backend API (default: `http://localhost:8000`).

## Testing

```bash
npm test           # Headless Playwright tests
npm run test:ui    # Interactive Playwright UI
```

## Project Structure

- `src/api/`: API client and helpers.
- `src/arenaApp.ts`: Main logic for the Dashboard.
- `src/replayApp.ts`: Main logic for the Replay Viewer.
- `src/replayPlayer.ts`: Game replay rendering engine.
