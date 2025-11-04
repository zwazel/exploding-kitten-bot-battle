# Exploding Kittens Replay Viewer

A TypeScript-based web application for visualizing and analyzing game replays from the Exploding Kittens bot battle simulations.

## Features

- 🎮 Load and visualize game replay JSON files
- ▶️ Play/Pause replay with adjustable speed (0.5x to 3x)
- ⏭️ Step forward through game events
- 📊 Real-time player status and card counts
- 🎯 Event-by-event game state visualization
- 📱 Responsive design for desktop and mobile
- 🚀 No server required - runs entirely in the browser

## Getting Started

### Prerequisites

- Node.js 20 or higher
- npm (comes with Node.js)

### Installation

1. Navigate to the replay-viewer directory:
   ```bash
   cd replay-viewer
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Development

Run the development server:

```bash
npm run dev
```

This will start a local development server at `http://localhost:5173` with hot module replacement.

### Building for Production

Build the application:

```bash
npm run build
```

The built files will be in the `dist/` directory and can be:
- Served by any static file server
- Deployed to GitHub Pages
- Opened directly in a browser (using `file://`)

### Preview Production Build

After building, preview the production build locally:

```bash
npm run preview
```

## Using the Replay Viewer

### Generating Replay Files

First, generate a replay file from the Python game engine:

```bash
cd ..  # Go back to the root directory
python3 main.py --test --replay my_game.json
```

This will create a `my_game.json` file containing the complete game replay.

### Loading and Playing Replays

1. Open the replay viewer in your browser
2. Click "📁 Load Replay File" and select your replay JSON file
3. Use the playback controls:
   - **⏹️ Stop**: Reset to the beginning
   - **▶️/⏸️ Play/Pause**: Auto-play through events
   - **⏭️ Step Forward**: Advance one event
   - **Speed slider**: Adjust playback speed (0.5x to 3x)

## Project Structure

```
replay-viewer/
├── src/
│   ├── main.ts          # Application entry point
│   ├── types.ts         # TypeScript type definitions
│   ├── replayPlayer.ts  # Replay playback logic
│   ├── renderer.ts      # UI rendering and visualization
│   └── style.css        # Application styles
├── tests/               # Playwright tests
│   ├── fixtures/        # Test data files
│   ├── basic-ui.spec.ts
│   ├── file-upload.spec.ts
│   └── playback-controls.spec.ts
├── public/              # Static assets
├── index.html           # HTML entry point
├── playwright.config.ts # Playwright configuration
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies and scripts
```

## Technology Stack

- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Vanilla JS/CSS**: No framework dependencies for simplicity and performance
- **Playwright**: End-to-end testing framework

## Testing

The replay viewer includes automated tests using Playwright.

### Running Tests

Run all tests:

```bash
npm test
```

Run tests with UI mode (interactive):

```bash
npm run test:ui
```

Run tests in headed mode (see the browser):

```bash
npm run test:headed
```

### Test Structure

Tests are located in the `tests/` directory:

```
tests/
├── fixtures/
│   └── test_replay.json  # Sample replay file for testing
├── basic-ui.spec.ts      # Tests for basic UI elements
├── file-upload.spec.ts   # Tests for file upload functionality
└── playback-controls.spec.ts  # Tests for playback controls
```

### Continuous Integration

Tests run automatically on:
- Pull requests to the main branch
- Commits to the main branch

The test workflow is defined in `.github/workflows/test-replay-viewer.yml`.

## Deployment

### GitHub Pages

The application is configured to deploy to GitHub Pages automatically when changes are pushed to the main branch.

To enable GitHub Pages:

1. Go to your repository settings
2. Navigate to "Pages" in the sidebar
3. Under "Build and deployment", select "GitHub Actions" as the source

The workflow will automatically build and deploy the replay viewer.

### Manual Deployment

You can deploy the built files from `dist/` to any static hosting service:

- GitHub Pages
- Netlify
- Vercel
- AWS S3
- Any web server (Apache, Nginx, etc.)

## Replay File Format

The replay viewer expects JSON files with the following structure:

```json
{
  "metadata": {
    "timestamp": "2025-11-03T12:00:00",
    "players": ["Player1", "Player2", "Player3"],
    "version": "1.0"
  },
  "events": [
    {
      "type": "game_setup",
      "deck_size": 33,
      "initial_hand_size": 7,
      "play_order": ["Player1", "Player2", "Player3"],
      "initial_hands": { ... }
    },
    {
      "type": "turn_start",
      "turn_number": 1,
      "player": "Player1",
      ...
    }
    // ... more events
  ],
  "winner": "Player1"
}
```

See the main repository README for complete event type documentation.

## Browser Support

The replay viewer works in all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is part of the Exploding Kittens Bot Battle repository.
