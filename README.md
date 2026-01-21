# Exploding Kitten Bot Battle

A bot battle card game framework for educational coding exercises. Students implement bots that compete against each other in Exploding Kittens.

## Features

- **Dynamic Bot Loading**: Bots are loaded at runtime from Python files
- **Anti-Cheat Protection**: Bots only see what they're allowed to see (own hand, discard pile, card counts)
- **Deterministic Randomness**: Seeded RNG for reproducible games
- **Event History**: Every action recorded, exportable to JSON for replay
- **Full Card Set**: All Exploding Kittens cards implemented (Nope, Attack, Favor, etc.)

## Setup

```bash
pip install -e ".[dev]"
```

### IDE Setup

If you see import errors (red squiggles) in your bot files, you need to tell your IDE where the game code is located.

**PyCharm:**
1. Right-click the `src` folder in the project view.
2. Select **Mark Directory as** > **Sources Root**.

**VS Code:**
1. Ensure you have installed the package using the command above.
2. Select the correct Python interpreter (the one where you installed the package).


## Running a Game

```bash
# Load all bots from ./bots directory
python -m game.main

# Specific bot files with copies (e.g., bot vs itself)
python -m game.main --bot bots/my_bot.py:3

# Combine directory + individual bots
python -m game.main --bots-dir ./bots --bot bots/test_bot.py:2

# Save game history for replay
python -m game.main --seed 42 --history game.json

# Run statistics mode (100 games by default)
python -m game.main --stats

# Run statistics with custom iteration count
python -m game.main --stats --iterations 500

# Run statistics with parallel workers for speed
python -m game.main --stats --iterations 10000 --workers 8

# Disable chat output for cleaner logs
python -m game.main --no-chat
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--bots-dir` | `./bots` | Directory with bot files |
| `--bot FILE[:N]` | - | Load bot file (N copies, default 1) |
| `--deck-config` | `configs/default_deck.json` | Deck configuration |
| `--seed` | Random | Seed for reproducibility |
| `--history` | - | Save history JSON |
| `--stats` | Off | Run statistics mode (runs verification first, disqualifies slow bots) |
| `--iterations` | `100` | Number of games to run in statistics mode |
| `--workers` | CPU count | Parallel workers for statistics mode |
| `--no-chat` | Off | Disable chat output (keeps console cleaner) |
| `--timeout` | `5.0` | Bot timeout in seconds (0 to disable). Used in verification run |

## Creating a Bot

Create a Python file in `bots/` implementing the `Bot` interface:

```python
from game.bots.base import Bot, Action, DrawCardAction, PlayCardAction, ChatAction
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent

class MyBot(Bot):
    @property
    def name(self) -> str:
        return "MyBot"
    
    def take_turn(self, view: BotView) -> Action:
        # Play a card, chat, or draw
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        # React to game events (optional)
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        # Play Nope card to cancel an action (optional)
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        # Where to put Exploding Kitten after defusing (0=top, next draw)
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        # Which card to give when targeted by Favor
        return view.my_hand[0]
```

## Bot Chat System

Bots can send chat messages during their turn using `view.say()`:

```python
def take_turn(self, view: BotView) -> Action:
    # Send a chat message - simple!
    view.say("Let's gooo!")
    
    # Then continue with your action
    return DrawCardAction()
```

**Chat Rules:**
- Bots can only chat during their own turn
- Just call `view.say()` and continue with your action
- Messages are truncated to 200 characters
- All bots can see chat messages via `view.recent_events`
- Chat events appear in game logs with `[CHAT]` prefix

See `bots/random_bot.py` for a working example with chat!

## Project Structure

```
├── src/game/           # Core game engine
│   ├── cards/          # Card implementations
│   ├── bots/           # Bot system
│   └── main.py         # CLI entry point
├── bots/               # User-created bots
├── configs/            # Deck configurations
└── tests/              # Test suite
```

