# Exploding Kitten Bot Battle

A bot battle card game framework for educational coding exercises. Students implement bots that compete against each other in a card game.

## Features

- **Dynamic Bot Loading**: Bots are loaded at runtime from the `bots/` directory
- **Anti-Cheat Protection**: Bots only see what they're allowed to see (their own hand, discard pile, card counts)
- **Deterministic Randomness**: Seeded RNG for reproducible games and testing
- **Event History**: Every action is recorded for future replay functionality
- **Extensible Card System**: Easy to add new card types with custom behavior
- **Configurable Decks**: JSON configuration files define card counts

## Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Project Structure

```
├── src/game/           # Core game engine
│   ├── cards/          # Card system
│   └── bots/           # Bot system
├── bots/               # User-created bots (loaded at runtime)
├── configs/            # Deck configuration files
└── tests/              # Test suite
```

## Creating a Bot

Create a Python file in the `bots/` directory that implements the `Bot` interface:

```python
from game.bots.base import Bot
from game.bots.view import BotView
from game.history import GameEvent

class MyBot(Bot):
    @property
    def name(self) -> str:
        return "MyBot"
    
    def take_turn(self, view: BotView) -> Action | None:
        # Your turn logic here
        pass
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        # React to game events
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        # Decide whether to play a reaction card
        return None
```

## Running a Game

```python
from game.engine import GameEngine

engine = GameEngine(seed=42)
engine.load_bots_from_directory("bots/")
engine.load_deck_config("configs/default_deck.json")
engine.run()
```
