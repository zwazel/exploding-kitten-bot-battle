# Arena Frontend

A Vite + TypeScript single page application that combines the classic Exploding Kittens replay viewer with the new arena dashboard. You can still upload local replay files without an account, while authenticated users can manage bots, trigger arena matches, and browse hosted replays.

## Features

- 🎮 **Replay viewer** – drop in a JSON replay file to animate every action.
- 🔐 **Authentication** – sign up/login to manage your arena bots.
- 🧰 **Multi-bot management** – create, select, and delete bots; uploads are tracked per bot with automatic versioning.
- 🤖 **Bot upload** – send a `.py` bot file to the backend; the arena instantly runs a match against other active bots.
- 📜 **Version history** – keep track of uploads and know which replays belong to each version.
- 📁 **Replay archive** – download or instantly open any hosted replay back in the viewer tab.
- 📱 Responsive design that works down to small viewports.

## Getting started

```bash
cd frontend
npm install
npm run dev
```

The development server runs on <http://localhost:5173>. Set `VITE_API_BASE_URL` in a `.env` file to point to your backend (defaults to `http://localhost:8000`).

### Testing

```bash
npm test           # headless Playwright run
npm run test:ui    # interactive Playwright mode
```

Playwright tests live in `frontend/tests/` and cover the core viewer behaviour as well as arena flows.

## Project structure

```
frontend/
├── src/
│   ├── api/            # API client helpers
│   ├── arenaApp.ts     # Arena dashboard controller
│   ├── replayApp.ts    # Replay viewer logic
│   ├── replayPlayer.ts # Existing playback engine
│   ├── renderer.ts     # Visual rendering helpers
│   └── style.css       # Global styles
├── tests/              # Playwright end-to-end tests
├── vite.config.ts
└── package.json
```

## Usage tips

- The viewer tab behaves exactly like the original tool – no login required.
- Uploading a bot version triggers a match immediately; the placements summary appears in the arena tab and the replay is available to view or download.
- Arena replays respect your current bot version history, so you can always tell which upload generated which game.

See the root `README.md` for instructions on running the backend service.
