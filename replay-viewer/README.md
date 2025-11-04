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
├── playback-controls.spec.ts  # Tests for playback controls
└── agent-jump.spec.ts    # Tests for hidden jump-to-step feature
```

### Hidden Jump-to-Step Feature (For Automated Testing)

The replay viewer includes a hidden feature for automated testing and agents that allows jumping forward to specific events without animations. This is useful for:

- Testing specific game states quickly
- Validating UI behavior at different points in the replay
- Debugging issues at specific event indices

**Accessing the Feature:**

The jump feature is implemented as a hidden input field with ID `agent-jump-to-event` and data-testid `agent-jump-to-event`.

```typescript
// In Playwright tests
const jumpInput = page.getByTestId('agent-jump-to-event');

// Jump to event index 50
await jumpInput.evaluate((el: HTMLInputElement) => {
  el.value = '50';
  el.dispatchEvent(new Event('input', { bubbles: true }));
});

await page.waitForTimeout(500);
```

**Important Constraints:**

- **Forward-only**: Can only jump to future events, not backward (prevents state inconsistencies)
- **Bounds checking**: Target index must be within valid range (0 to events.length - 1)
- **Pauses playback**: Automatically pauses if currently playing
- **No animations**: Events are processed but animations are skipped for speed

**Use Cases:**

```typescript
// Pseudo-code for illustration only. See above for actual usage via input field and event dispatch.
// Jump to a specific turn to test turn mechanics
await jumpToEvent(50);

// Skip to near the end to test game-over behavior
const totalEvents = getTotalEventCount();
await jumpToEvent(totalEvents - 5);

// Quickly validate state at multiple points
for (const checkpoint of [10, 25, 50, 75]) {
  await jumpToEvent(checkpoint);
  await validateGameState();
}
```

This feature is intentionally hidden from the UI to prevent user confusion and is only accessible via automated testing tools.

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

## Architecture & Implementation Notes

### Event Processing and Synchronization

The replay viewer processes events from the replay JSON file sequentially. Important considerations:

#### Event Display vs Replay Events
- **Replay events** are the events stored in the JSON file (e.g., `game_setup`, `turn_start`, `combo_play`, `card_play`)
- **Frontend animations** may render multiple cards or sub-animations for a single replay event
- For example, a `combo_play` event with 3 cards will trigger 3 separate card animations, but counts as ONE event
- The event counter always reflects the replay file's event index, not the number of animation frames

#### Asynchronous Processing
- Event rendering is fully asynchronous to support smooth animations
- The `isProcessingEvent` flag prevents concurrent event processing
- Event counter updates occur in a `finally` block AFTER the processing flag is cleared
- This ensures tests can rely on the counter appearing only when the system is ready for the next event

#### Testing Considerations  
- Playwright tests should wait for UI state changes (e.g., counter updates, button enabled state)
- For rapid sequential operations, prefer using the agent jump functionality over multiple step clicks
- The step-forward button is disabled during event processing to prevent race conditions

## Browser Support

The replay viewer works in all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is part of the Exploding Kittens Bot Battle repository.
