# Agent Guidelines

## Project Overview

This is a Python-based bot battle card game framework. Students write bots that compete against each other.

## Key Patterns

### Type Safety
- **Always** declare types for all variables, parameters, and return values
- Use `pyright` in strict mode for type checking
- Prefer `tuple` over `list` for immutable sequences exposed to bots

### Anti-Cheat Architecture
- `GameState` is **never** exposed directly to bots
- Bots receive a `BotView` - a safe, read-only snapshot
- `BotView` only contains information the bot is allowed to see

### Card System
- Each card type is a class extending `Card` base class
- Cards define their own behavior via `can_play()`, `execute()`, etc.
- Card instances are created from the `CardRegistry` based on config

### Event History
- Every game action creates a `GameEvent`
- Events are recorded in `GameHistory` for future replay
- Use `GameEvent` for both history and bot notifications

### Deterministic RNG
- All randomness goes through `DeterministicRNG`
- Same seed = same game outcome (given same bot behavior)
- Useful for testing and debugging

## File Organization

```
src/game/           # Core engine (protected)
  ├── cards/        # Card base class and registry
  └── bots/         # Bot interface and loader
bots/               # User bots (loaded at runtime)
configs/            # Deck configurations
tests/              # Test suite
```

## Testing

- Use seeded RNG for deterministic tests
- Test cards in isolation before integration
- Verify `BotView` doesn't leak protected information

## Game Setup Rules

Per official Exploding Kittens rules, `setup_game` follows this flow:
1. Remove Exploding Kittens and Defuse cards from deck
2. Validate Defuse count ≥ (players + 1) - **warns and auto-adds if needed**
3. Generate exactly **(players - 1)** Exploding Kittens at runtime
4. Deal initial hands (7 cards) from safe cards only
5. Give each player 1 Defuse card
6. Shuffle Exploding Kittens and remaining Defuse cards back into deck

**Note:** `ExplodingKittenCard` should NOT be in deck config - always auto-generated.

## Chat System

Bots can "talk" during their turn using `view.say()`:

### Key Points
- Call `view.say(message)` during `take_turn()` to send a chat message
- Messages are truncated to 200 characters to prevent spam
- Recorded in game history as `EventType.BOT_CHAT`
- Bots see chat via `view.recent_events` in subsequent calls to `on_event`
- Game logs show `[GAME]` prefix, chat shows `[CHAT]` prefix

### Implementation Pattern
The `BotView` object passed to `take_turn()` has a `say()` method:
```python
def take_turn(self, view: BotView) -> Action:
    view.say("Hello everyone!")  # Send a chat message
    return DrawCardAction()      # Continue with action
```

When `view.say()` is called, the engine:
1. Logs the message with `[CHAT]` prefix
2. Records a `BOT_CHAT` event in history
3. Notifies all bots via `on_event`

Note: Chat is only available during `take_turn()`. Views passed to other methods
(like `on_event` or `react`) do not have chat enabled.
