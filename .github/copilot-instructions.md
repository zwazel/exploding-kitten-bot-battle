# GitHub Copilot Instructions for Exploding Kitten Bot Battle

## Project Overview

This is a Python-based simulation of the "Exploding Kittens" card game where autonomous bots compete against each other. The project serves as an educational platform for students to create and test game-playing AI strategies.

## Repository Structure

```
exploding-kitten-bot-battle/
├── game/               # Core game engine (DO NOT MODIFY)
│   ├── bot.py         # Base Bot class that all bots inherit from
│   ├── cards.py       # Card types and Card class definitions
│   ├── game_state.py  # GameState and CardCounts classes
│   ├── deck.py        # Deck management and operations
│   ├── game_engine.py # Main game loop and mechanics
│   ├── config.py      # Game configuration settings
│   └── replay_recorder.py # Game replay recording functionality
├── bots/              # Bot implementations (ADD YOUR BOTS HERE)
│   ├── RandomBot.py   # Example: plays randomly
│   ├── CautiousBot.py # Example: plays defensively
│   └── AggressiveBot.py # Example: plays aggressively
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
- **Current:** Python 3.12.3 is being used
- **Dependencies:** No external runtime dependencies (pure Python standard library)

### Testing
Always run tests before and after making changes:
```bash
python3 -m unittest tests.test_game -v
```

All 70 tests must pass. Do not break existing tests.

### Running the Game
```bash
# Normal mode (with pauses)
python3 main.py

# Test mode (automatic, no pauses)
python3 main.py --test

# With replay recording
python3 main.py --test --replay game_replay.json
```

### Linting (Optional)
Optional development tools are listed in `requirements.txt`:
- `black` for code formatting
- `flake8` for linting
- `pytest` as an alternative test runner

## Code Modification Rules

### ⚠️ CRITICAL: What NOT to Modify
- **DO NOT modify** any code in the `game/` directory unless fixing a critical bug in the game engine
- **DO NOT modify** the base `Bot` class interface
- **DO NOT modify** existing tests unless they are incorrect
- **DO NOT change** the game rules or mechanics
- **DO NOT modify** other students' bots in the `bots/` directory

### ✅ What Can Be Modified
- **ADD new bots** to the `bots/` directory
- **MODIFY your own bot** files in `bots/`
- **ADD new tests** that validate bot behavior
- **UPDATE documentation** (README.md, CONTRIBUTING.md) for clarity

## Creating a New Bot

### File Naming Convention
- **File name:** `YourBotName.py` (e.g., `SmartBot.py`)
- **Class name:** Must match file name exactly (e.g., `class SmartBot(Bot):`)
- **Location:** Place in `bots/` directory

### Required Imports
```python
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext
```

### Required Methods to Implement
All bots MUST implement these 8 methods from the `Bot` base class:

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

8. **`should_play_nope(state: GameState, action_description: str) -> bool`**
   - Called when another player's action can be noped
   - Return True to play Nope, False otherwise

### Optional Override
**`on_action_played(state: GameState, action_description: str, actor: Bot) -> None`**
- Called when ANY action occurs in the game
- Use to track game state, opponent behavior, etc.
- Helps with strategy and decision-making

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
    
    def play(self, state: GameState) -> Optional[Card]:
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
state.total_cards_in_deck: CardCounts  # Original card counts
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
   # ❌ BAD
   def play(self, state: GameState) -> Optional[Card]:
       while True:  # Never returns None!
           return self.hand[0]
   
   # ✅ GOOD
   def play(self, state: GameState) -> Optional[Card]:
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

## Questions or Issues?

- Check README.md for game rules and API
- Check CONTRIBUTING.md for strategy tips
- Look at example bots for patterns
- Run tests to verify game behavior
- Use GameState to access game information

## Summary for Copilot

When assisting with this repository:
1. **Never modify** the game engine in `game/` directory
2. **Always validate** that bots implement all required methods
3. **Always test** with `python3 -m unittest tests.test_game -v` before committing
4. **Follow** the Bot class interface exactly
5. **Reference** existing example bots for patterns
6. **Validate** combos don't include DEFUSE or EXPLODING_KITTEN
7. **Ensure** bot class name matches file name
8. **Keep** changes minimal and focused on bot logic only
