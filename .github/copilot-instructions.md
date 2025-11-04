# GitHub Copilot Instructions for Exploding Kitten Bot Battle

## Project Overview

This is a Python-based simulation of the "Exploding Kittens" card game where autonomous bots compete against each other. The project serves as an educational platform for students to create and test game-playing AI strategies.

## Repository Structure

```
exploding-kitten-bot-battle/
├── game/               # Core game engine (DO NOT MODIFY)
│   ├── bot.py         # Base Bot class that all bots inherit from
│   ├── cards.py       # Card types and Card class definitions
│   ├── game_state.py  # GameState class for game information
│   ├── deck.py        # Deck management and operations
│   ├── game_engine.py # Main game loop and mechanics
│   ├── config.py      # Game configuration settings
│   └── replay_recorder.py # Game replay recording functionality
├── bots/              # Bot implementations (ADD YOUR BOTS HERE)
│   ├── RandomBot.py   # Example: plays randomly
│   ├── CautiousBot.py # Example: plays defensively
│   └── AggressiveBot.py # Example: plays aggressively
├── replay-viewer/     # TypeScript web app for viewing replays (DO NOT MODIFY unless fixing replay viewer)
│   ├── src/           # TypeScript source files
│   ├── public/        # Static assets
│   ├── dist/          # Built files (generated, not in git)
│   ├── index.html     # HTML entry point
│   ├── package.json   # Node.js dependencies
│   ├── vite.config.ts # Vite build configuration
│   ├── README.md      # Replay viewer documentation
│   └── QUICKSTART.md  # Quick start guide for replay viewer
├── tests/             # Unit tests for game components
│   └── test_game.py   # Comprehensive test suite
├── main.py            # Entry point to run the game
├── requirements.txt   # Python dependencies (optional dev tools)
├── README.md          # User documentation
└── CONTRIBUTING.md    # Bot creation guide
```

## Development Guidelines

### Python Version
- **Required:** Python 3.8 or higher
- **Tested with:** Python 3.12.3
- **Dependencies:** No external runtime dependencies (pure Python standard library)

### Testing
Always run tests before and after making changes:
```bash
python3 -m unittest tests.test_game -v
```

All existing tests must pass. Do not break existing tests.

### Running the Game
```bash
# Normal mode (with pauses)
python3 main.py

# Test mode (automatic, no pauses)
python3 main.py --test

# With replay recording (generates JSON file for replay viewer)
python3 main.py --test --replay game_replay.json

# Statistics mode (run multiple games and collect statistics)
python3 main.py --stats statistics.json --runs 100
```

### Statistics Mode
The statistics mode runs multiple games to evaluate bot performance:
- **Flag:** `--stats <filename>`
- **Runs:** `--runs <number>` (default: 100)
- **Incompatible with:** `--replay` (cannot use both)
- **Output:** JSON file with comprehensive statistics and console summary

**Statistics Tracked:**
- Win count and win rate per bot
- Average placement (1.0 = always wins)
- Placement distribution (1st, 2nd, 3rd, etc.)
- Total games played

**Example:**
```bash
python3 main.py --stats results.json --runs 200
```

The game runs in silent mode (verbose=False) for performance, showing only progress updates every 10 games.

### Generating Replay Files for Testing
To generate a replay file that can be used with the replay viewer:
```bash
# Generate a replay file from a game simulation
python3 main.py --test --replay my_game.json

# This creates a JSON file containing all game events
# Use this file to test the replay viewer
```

**Creating Custom Test Replay Files (For Agents):**
Agents can manually create minimal test replay files to test specific scenarios without waiting for full game simulations. This saves significant time during testing. Example minimal replay file:

```json
{
  "metadata": {
    "timestamp": "2025-11-04T12:00:00",
    "players": ["TestBot1", "TestBot2"],
    "version": "1.0"
  },
  "events": [
    {
      "type": "game_setup",
      "deck_size": 10,
      "initial_hand_size": 3,
      "play_order": ["TestBot1", "TestBot2"],
      "initial_hands": {
        "TestBot1": ["SKIP", "NOPE", "ATTACK"],
        "TestBot2": ["SKIP", "FAVOR", "DEFUSE"]
      }
    },
    {
      "type": "turn_start",
      "turn_number": 1,
      "player": "TestBot1",
      "turns_remaining": 1,
      "hand_size": 3,
      "cards_in_deck": 10
    },
    {
      "type": "card_play",
      "turn_number": 1,
      "player": "TestBot1",
      "card": "SKIP"
    }
  ],
  "winner": null
}
```

Save this to a `.json` file and load it in the replay viewer to test specific UI behaviors quickly.

### Linting (Optional)
Optional development tools are listed in `requirements.txt`:
- `black` for code formatting
- `flake8` for linting
- `pytest` as an alternative test runner

### Replay Viewer (TypeScript Web App)
The replay viewer is a separate TypeScript/Vite application for visualizing game replays:
```bash
cd replay-viewer
npm install          # Install dependencies (first time only)
npm run dev          # Start development server at http://localhost:5173
npm run build        # Build for production (output to dist/)
npm run preview      # Preview production build
```

**Testing the Replay Viewer:**
1. Generate a replay file: `python3 main.py --test --replay test_replay.json`
2. Start the replay viewer: `cd replay-viewer && npm run dev`
3. Load the replay file in the browser at http://localhost:5173

**Agent Jump-to-Step Feature (For Automated Testing):**
The replay viewer includes a hidden jump-to-step feature for agents and automated testing. This allows jumping forward to a specific event without waiting for animations, significantly speeding up testing.

To use with Playwright:
```typescript
// Access the hidden input field
const jumpInput = page.getByTestId('agent-jump-to-event');

// Jump to event index 50 (0-indexed)
await jumpInput.evaluate((el: HTMLInputElement) => {
  el.value = '50';
  el.dispatchEvent(new Event('input', { bubbles: true }));
});

// Wait for the jump to complete
await page.waitForTimeout(500);
```

**Important constraints:**
- Jump only works forward, not backward (prevents state inconsistencies)
- Target index must be within valid bounds (0 to events.length - 1)
- Jumps will pause playback if currently playing
- All events are processed, just without animations

This feature is NOT visible in the UI and is only accessible via the `agent-jump-to-event` input field using Playwright or similar automation tools.

**GitHub Pages Deployment:**
- The replay viewer automatically deploys to GitHub Pages when pushed to main branch
- Workflow: `.github/workflows/deploy-pages.yml`
- Built files from `replay-viewer/dist/` are deployed
- Do NOT commit the `dist/` directory to git (it's generated)

## Code Modification Rules

### For Students Creating Bots
These rules apply to students learning to create bots (described in README.md):
- **DO NOT modify** any code in the `game/` directory - use the game engine as-is
- **DO NOT modify** the base `Bot` class interface - inherit from it correctly
- **DO NOT modify** other students' bots in the `bots/` directory
- **ONLY create** your own bot files in the `bots/` directory

### For Contributors/Agents (You!)
As a contributor/agent, you have full access to modify any part of the codebase:
- ✅ **CAN modify** game engine code in `game/` directory
- ✅ **CAN modify** the replay viewer in `replay-viewer/` directory
- ✅ **CAN modify** the `Bot` class interface (backwards compatibility not required)
- ✅ **CAN modify** tests and add new tests
- ✅ **CAN modify** game rules and mechanics
- ✅ **CAN modify** documentation
- ✅ **CAN add/modify** bot examples
- ⚠️ **DO NOT commit** the `replay-viewer/dist/` directory (it's auto-generated)

## Creating a New Bot

### File Naming Convention
- **File name:** `YourBotName.py` (e.g., `SmartBot.py`)
- **Class name:** Must match file name exactly (e.g., `class SmartBot(Bot):`)
- **Location:** Place in `bots/` directory

### Required Imports
```python
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext, GameAction
```

### Required Methods to Implement
All bots MUST implement these 9 methods from the `Bot` base class:

1. **`play(state: GameState) -> Optional[Union[Card, List[Card]]]`**
   - Called repeatedly during play phase
   - Return a Card to play, a List[Card] for combos, or None to end play phase
   - Can be called multiple times per turn

2. **`handle_exploding_kitten(state: GameState) -> int`**
   - Called when you draw Exploding Kitten and have Defuse
   - Return position to insert Exploding Kitten (0 = top, state.cards_left_to_draw = bottom)

3. **`see_the_future(state: GameState, top_three: List[Card]) -> None`**
   - Called when you play See the Future card
   - Use this info for strategy (store in instance variables)

4. **`choose_target(state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]`**
   - Called when you need to select a target for Favor or combo
   - Return the target Bot or None

5. **`choose_card_from_hand(state: GameState) -> Optional[Card]`**
   - Called when you must give a card (Favor or 3-of-a-kind request)
   - Return the Card to give from your hand

6. **`choose_card_type(state: GameState) -> Optional[CardType]`**
   - Called for 3-of-a-kind combo to request specific card type
   - Return the CardType you want to request

7. **`choose_from_discard(state: GameState, discard_pile: List[Card]) -> Optional[Card]`**
   - Called for 5-unique combo to pick from discard pile
   - Return the Card to take

8. **`should_play_nope(state: GameState, action: GameAction) -> bool`**
   - Called when another player's action can be noped
   - `action` is a GameAction object containing action details (action_type, card, actor, target, etc.)
   - Return True to play Nope, False otherwise

9. **`on_action_played(state: GameState, action: GameAction, actor: Bot) -> None`**
   - Called when ANY action occurs in the game (for all bots)
   - `action` is a GameAction object containing action details (action_type, card, actor, target, etc.)
   - `actor` is the Bot who performed the action
   - Use to track game state, opponent behavior, and game history
   - Can simply `pass` if you don't need to track actions

## Code Style Guidelines

### General Python Style
- Follow PEP 8 conventions
- Use type hints for all method signatures
- Write descriptive variable names
- Add docstrings to classes and complex methods

### Bot-Specific Guidelines
```python
class YourBot(Bot):
    """Brief description of bot's strategy."""
    
    def __init__(self, name: str):
        super().__init__(name)
        # Initialize instance variables for strategy
        self.last_seen_cards = []
        self.known_threats = []
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """Choose which card to play based on game state."""
        # Always check if you have the card before returning it
        if self.has_card_type(CardType.SKIP):
            # Your logic here
            pass
        return None
```

### Common Patterns
```python
# Check if you have a card type
if self.has_card_type(CardType.DEFUSE):
    # Do something

# Check if you have a specific card
if self.has_card(some_card):
    # Do something

# Access your hand
for card in self.hand:
    if card.card_type == CardType.NOPE:
        # Do something

# Safe card selection
defuse_cards = [c for c in self.hand if c.card_type == CardType.DEFUSE]
if defuse_cards:
    return defuse_cards[0]
```

## Game Mechanics Reference

### Card Types (Enum: CardType)
- **Action Cards:** EXPLODING_KITTEN, DEFUSE, SKIP, SEE_THE_FUTURE, SHUFFLE, ATTACK, FAVOR, NOPE
- **Cat Cards (for combos):** TACOCAT, CATTERMELON, HAIRY_POTATO_CAT, BEARD_CAT, RAINBOW_RALPHING_CAT

### Combo Types (Enum: ComboType)
- **TWO_OF_A_KIND:** 2 identical cards → steal random card from target
- **THREE_OF_A_KIND:** 3 identical cards → request specific card type from target
- **FIVE_UNIQUE:** 5 different cards → take any card from discard pile

### Invalid Combos
- ❌ Cannot use DEFUSE in combos
- ❌ Cannot use EXPLODING_KITTEN in combos
- ❌ 5-unique combo cannot include DEFUSE

### Target Context (Enum: TargetContext)
- FAVOR: choosing target for Favor card
- TWO_OF_A_KIND: choosing target for 2-of-a-kind combo
- THREE_OF_A_KIND: choosing target for 3-of-a-kind combo

## GameState API

When your bot receives `GameState`, it contains:
```python
state.initial_card_counts: Dict[CardType, int]  # Original card counts by type
state.cards_left_to_draw: int          # Cards remaining in deck
state.was_last_card_exploding_kitten: bool  # If last drawn kitten was returned
state.history_of_played_cards: List[Card]   # All cards played so far
state.alive_bots: int                  # Number of bots still alive
```

Use this to:
- Calculate probabilities of drawing Exploding Kitten
- Track which cards have been played
- Infer deck composition
- Make strategic decisions

## Testing Your Bot

### Basic Validation
```bash
# Test with just your bot (it plays against itself)
python3 main.py --test

# Test with example bots
python3 main.py --test
```

### Unit Testing
Create focused tests for your bot's logic:
```python
# In tests/test_my_bot.py
import unittest
from bots.MyBot import MyBot
from game import GameState, Card, CardType

class TestMyBot(unittest.TestCase):
    def test_bot_plays_skip_when_threatened(self):
        bot = MyBot("TestBot")
        # Add test logic
        self.assertIsNotNone(bot.play(state))
```

Run with:
```bash
python3 -m unittest tests.test_my_bot -v
```

## Common Pitfalls to Avoid

1. **Returning cards you don't have**
   ```python
   # ❌ BAD
   return Card(CardType.SKIP)  # May not have Skip
   
   # ✅ GOOD
   skip_cards = [c for c in self.hand if c.card_type == CardType.SKIP]
   if skip_cards:
       return skip_cards[0]
   return None
   ```

2. **Infinite loops in play()**
   ```python
   # ❌ BAD - Never returns None, will be called indefinitely
   def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
       if self.hand:
           return self.hand[0]  # Always returns a card!
   
   # ✅ GOOD - Eventually returns None to end play phase
   def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
       if self.has_card_type(CardType.SKIP):
           # Return skip card
           pass
       return None  # Always eventually return None
   ```

3. **Not validating combo cards**
   ```python
   # ❌ BAD - May try to combo with DEFUSE
   cards = [c for c in self.hand if c.card_type == CardType.DEFUSE]
   if len(cards) >= 2:
       return cards[:2]  # Invalid!
   
   # ✅ GOOD - Only combo with valid cards
   cards = [c for c in self.hand if c.card_type == CardType.ATTACK]
   if len(cards) >= 2:
       return cards[:2]
   ```

4. **Forgetting to handle edge cases**
   - Empty hand
   - Empty deck
   - No valid targets
   - Last player standing

## Git Workflow

When adding a new bot:
1. Create your bot file in `bots/`
2. Test thoroughly with `python3 main.py --test`
3. Run unit tests: `python3 -m unittest tests.test_game -v`
4. Commit only your bot file (do not commit game engine changes unless fixing bugs)

## Additional Resources

- **README.md:** Complete game rules, API documentation, examples
- **CONTRIBUTING.md:** Detailed bot creation guide with strategies
- **bots/CautiousBot.py:** Well-commented example of defensive strategy
- **bots/AggressiveBot.py:** Example of offensive strategy with combos
- **bots/RandomBot.py:** Minimal example showing basic structure
- **replay-viewer/README.md:** Replay viewer documentation and features
- **replay-viewer/QUICKSTART.md:** Quick start guide for the replay viewer

## Replay Viewer

The project includes a TypeScript-based web application for visualizing game replays:

### Purpose
- Visualize game replays with animations and interactive controls
- Analyze bot strategies and game flow
- Debug bot behavior by seeing exact game events

### Technology Stack
- TypeScript with Vite for fast development
- No framework dependencies (vanilla JS/CSS)
- Node.js 20+ required

### Key Files
- `replay-viewer/src/main.ts` - Application entry point
- `replay-viewer/src/types.ts` - TypeScript type definitions
- `replay-viewer/src/replayPlayer.ts` - Replay playback logic
- `replay-viewer/src/renderer.ts` - UI rendering and visualization

### Working with Replay Viewer
When making changes to the replay viewer:
1. Generate a test replay: `python3 main.py --test --replay test.json`
2. Start dev server: `cd replay-viewer && npm run dev`
3. Load the replay in browser at http://localhost:5173
4. Test all playback controls (play, pause, step, speed adjustment)
5. Build for production: `npm run build` (output to `dist/`)
6. Never commit the `dist/` directory (it's auto-generated by CI/CD)

### Deployment
- Automatic deployment to GitHub Pages via `.github/workflows/deploy-pages.yml`
- Triggers on push to main branch
- Builds `replay-viewer/dist/` and deploys to Pages

## Questions or Issues?

- Check README.md for game rules and API
- Check CONTRIBUTING.md for strategy tips
- Look at example bots for patterns
- Run tests to verify game behavior
- Use GameState to access game information

## Summary for Copilot

When assisting with this repository:
1. **You can modify any part** of the codebase (game engine, replay viewer, Bot interface, etc.)
2. **Backwards compatibility** is not required - feel free to make breaking changes
3. **Always test** with `python3 -m unittest tests.test_game -v` before committing
4. **Update tests** when you change functionality
5. **Generate replay files** with `python3 main.py --test --replay <filename>.json` to test replay viewer
6. **Never commit** `replay-viewer/dist/` directory (auto-generated)
7. **Student-facing docs** (README.md, CONTRIBUTING.md) explain rules for students creating bots
8. **These instructions** are for you as a contributor/agent - you have full access
