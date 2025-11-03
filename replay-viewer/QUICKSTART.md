# Quick Start Guide

This guide will help you get started with the Exploding Kittens Replay Viewer.

## Prerequisites

- Python 3.8+ (for generating replay files)
- Node.js 20+ and npm (for running the replay viewer)

## Step 1: Generate a Replay

First, run a game and save the replay to a JSON file:

```bash
# From the repository root
python3 main.py --test --replay my_game.json
```

This will:
- Load all available bots
- Run a complete game simulation
- Save all game events to `my_game.json`

## Step 2: Start the Replay Viewer

```bash
# Navigate to the replay viewer
cd replay-viewer

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The replay viewer will open at `http://localhost:5173`

## Step 3: Load and Watch the Replay

1. Click the **"📁 Load Replay File"** button
2. Select your `my_game.json` file
3. Use the playback controls:
   - **▶️** to auto-play
   - **⏸️** to pause
   - **⏭️** to step forward one event
   - **⏮️** to step backward one event
   - **Speed slider** to adjust playback speed
   - **Event slider** to jump to any point in the game

## Production Build

To build for deployment:

```bash
cd replay-viewer
npm run build
```

The built files will be in `replay-viewer/dist/` and can be:
- Deployed to GitHub Pages
- Served by any web server
- Opened directly in a browser

## Troubleshooting

### "Module not found" errors
Make sure you ran `npm install` in the `replay-viewer` directory.

### Replay file won't load
Ensure your JSON file was generated using the `--replay` flag with the Python game engine.

### Changes not showing up
If you're developing, the dev server has hot reload. Just save your files and the browser will update automatically.

## Next Steps

- Read the full [Replay Viewer README](README.md)
- Check out the [Main Project README](../README.md) for game rules
- Create your own bot and generate more replays!
