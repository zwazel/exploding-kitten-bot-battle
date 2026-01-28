# Exploding Kitten Bot Battle

A bot battle card game framework for educational coding exercises. Students implement bots that compete against each other in Exploding Kittens.

## Features

- **Dynamic Bot Loading**: Bots are loaded at runtime from Python files
- **Anti-Cheat Protection**: Bots only see what they're allowed to see (own hand, discard pile, card counts)
- **Deterministic Randomness**: Seeded RNG for reproducible games
- **Event History**: Every action recorded, exportable to JSON for replay
- **Full Card Set**: All Exploding Kittens cards implemented (Nope, Attack, Favor, etc.)

## Setup

> ⚠️ **IMPORTANT:** You MUST run this command before anything else works!

```bash
pip install -e ".[dev]"
```

This installs the game module so Python can find it. Run this **once** from the project root folder.

### Troubleshooting: "No module named 'game'"

If you see this error when running `python -m game.main`:

```
ModuleNotFoundError: No module named 'game'
```

**Causes & Solutions:**

| Cause                         | Solution                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------- |
| Didn't run `pip install -e .` | Run `pip install -e ".[dev]"` from the project root                             |
| Wrong terminal/environment    | Make sure you're in the project folder and using the correct Python environment |
| Using a different Python      | Check with `where python` (Windows) — use the same Python you installed to      |

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

| Option           | Default                     | Description                                                           |
| ---------------- | --------------------------- | --------------------------------------------------------------------- |
| `--bots-dir`     | `./bots`                    | Directory with bot files                                              |
| `--bot FILE[:N]` | -                           | Load bot file (N copies, default 1)                                   |
| `--deck-config`  | `configs/default_deck.json` | Deck configuration                                                    |
| `--seed`         | Random                      | Seed for reproducibility                                              |
| `--history`      | -                           | Save history JSON                                                     |
| `--stats`        | Off                         | Run statistics mode (runs verification first, disqualifies slow bots) |
| `--iterations`   | `100`                       | Number of games to run in statistics mode                             |
| `--workers`      | CPU count                   | Parallel workers for statistics mode                                  |
| `--no-chat`      | Off                         | Disable chat output (keeps console cleaner)                           |
| `--timeout`      | `5.0`                       | Bot timeout in seconds (0 to disable). Used in verification run       |

## Creating a Bot

Create a Python file in `bots/` implementing the `Bot` interface. See `bots/random_bot.py` for a fully documented reference implementation!

### Required Imports

```python
from game.bots.base import (
    Bot,              # Base class (required)
    Action,           # Type alias for all actions
    DrawCardAction,   # End turn by drawing
    PlayCardAction,   # Play a single card
    PlayComboAction,  # Play multiple cards as a combo
)
from game.bots.view import BotView       # Your view of the game
from game.cards.base import Card          # Card objects
from game.history import GameEvent, EventType  # Event tracking
```

### Bot Template

```python
class MyBot(Bot):
    @property
    def name(self) -> str:
        """Return your bot's display name."""
        return "MyBot"
    
    def take_turn(self, view: BotView) -> Action:
        """
        Called when it's your turn.
        
        Available via view:
        - view.my_hand: Your cards (tuple of Card objects)
        - view.my_id: Your player ID
        - view.other_players: IDs of alive opponents
        - view.draw_pile_count: Cards remaining in deck
        - view.discard_pile: Visible discard pile
        - view.other_player_card_counts: Card count per opponent
        - view.say(message): Send a chat message
        
        MUST return DrawCardAction() to end your turn!
        """
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """
        Called for every game event (informational only).
        
        Useful event types:
        - EventType.CARD_PLAYED
        - EventType.CARD_DRAWN
        - EventType.PLAYER_ELIMINATED
        - EventType.DECK_SHUFFLED
        """
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Called during reaction rounds.
        Return PlayCardAction with a Nope card to cancel, or None to pass.
        """
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """
        Choose where to reinsert the Exploding Kitten after defusing.
        0 = top (next draw), draw_pile_size = bottom (safest).
        """
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """Choose which card to give when targeted by Favor."""
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        """
        Called when you're about to explode (no Defuse).
        Use view.say() for your last words!
        """
        view.say("Goodbye cruel world!")
```

### Card Combos

Bots can play card combos using `PlayComboAction`:

| Combo               | Cards Required           | Effect                                 |
| ------------------- | ------------------------ | -------------------------------------- |
| **Two of a Kind**   | 2 cards, same type       | Steal random card from target          |
| **Three of a Kind** | 3 cards, same type       | Name a card type, steal it from target |
| **Five Different**  | 5 cards, different types | Take any card from discard pile        |

```python
# Example: Playing a two-of-a-kind combo
cat_cards = [c for c in view.my_hand if c.card_type == "TacoCatCard"]
if len(cat_cards) >= 2 and view.other_players:
    target = view.other_players[0]
    return PlayComboAction(cards=tuple(cat_cards[:2]), target_player_id=target)
```

### Playing Cards

```python
# Find playable cards during your turn
# is_own_turn=True: filters for cards you can play proactively on your turn
# is_own_turn=False: would filter for reaction cards (but use react() for that)
playable = [c for c in view.my_hand if c.can_play(view, is_own_turn=True)]

# Play a simple card
return PlayCardAction(card=playable[0])

# Play a card that targets a player (Favor, Attack)
return PlayCardAction(card=favor_card, target_player_id=target_id)
```

## Bot Chat System

Bots can send chat messages anytime using `view.say()`:

```python
def take_turn(self, view: BotView) -> Action:
    view.say("Let's gooo!")  # Send chat message
    return DrawCardAction()  # Continue with action

def on_explode(self, view: BotView) -> None:
    view.say("NOOOOO!")  # Famous last words
```

**Chat Rules:**
- Call `view.say()` in any bot method (`take_turn`, `react`, `on_event`, etc.)
- Messages are truncated to 200 characters
- All bots see chat via `view.recent_events`
- Logs show `[CHAT]` prefix for chat, `[GAME]` for game events
- **Tip:** Avoid responding to `BOT_CHAT` events in `on_event` to prevent infinite loops!

See `bots/random_bot.py` for a complete example with chat integration!

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

