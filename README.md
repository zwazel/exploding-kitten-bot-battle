# exploding-kitten-bot-battle

## Project Overview

This project is a simulation of the popular card game "Exploding Kittens" where bots compete against each other autonomously. The game logic and rules are fully implemented, and your task is to create a bot that can play strategically to win!

## Table of Contents

- [Game Rules](#game-rules)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Creating Your Own Bot](#creating-your-own-bot)
- [Running the Game](#running-the-game)
- [Running Tests](#running-tests)
- [Code Overview](#code-overview)

## Game Rules

- Each player (bot) starts with a hand of 7 cards, including 1 Defuse card.
- Players take turns in random order.
- On each turn, a player can:
  1. **Play cards** from their hand (optional)
  2. **Draw a card** from the deck (required, unless Skip is played)
- If a player draws an **Exploding Kitten**:
  - They must use a **Defuse card** to avoid elimination
  - If they have a Defuse card, they can place the Exploding Kitten back in the deck at any position
  - If they don't have a Defuse card, they are eliminated from the game
- The last player remaining wins the game

### Card Types

#### Action Cards
- **Exploding Kitten**: Eliminates you unless you have a Defuse card
- **Defuse**: Saves you from an Exploding Kitten (1 per player initially)
- **Skip**: End your turn without drawing a card
- **See the Future**: Look at the top 3 cards of the deck
- **Shuffle**: Shuffle the deck
- **Attack**: End your turn without drawing; next player takes 2 turns
- **Favor**: Target player chooses which card to give you
- **Nope**: Cancel any action (except defusing). Can be chained!

#### Cat Cards (for Combos)
- **Tacocat**: No effect alone, use for combos
- **Cattermelon**: No effect alone, use for combos
- **Hairy Potato Cat**: No effect alone, use for combos
- **Beard Cat**: No effect alone, use for combos
- **Rainbow-Ralphing Cat**: No effect alone, use for combos

### Combo System

You can play multiple cards of the same type (or 5 unique cards) to perform special actions:

#### 2-of-a-Kind Combo
- Play 2 cards of the exact same type
- **Effect**: Randomly steal a card from any target player
- Can use any card type (2 Attacks, 2 Skips, 2 Tacocats, etc.)
- Card effects do NOT trigger when played as combo

#### 3-of-a-Kind Combo
- Play 3 cards of the exact same type
- **Effect**: Request a specific card type from a target player
- If target has that card type, they must give you one
- If target doesn't have it, nothing happens

#### 5-Unique Cards Combo
- Play 5 cards of different types
- **Effect**: Take any card from the discard pile
- Example: 1 Attack, 1 Skip, 1 Shuffle, 1 Tacocat, 1 Favor

**Note**: All combos can be Noped by other players!

### Nope Card Mechanics

- **Nope** cards can cancel any action except defusing an Exploding Kitten
- Nope cards can be played at any time when another player plays an action
- **Nope chains**: A Nope can be Noped, which can be Noped again, endlessly (as long as players have Nope cards)
- Players are notified of actions in play order and can respond
- Odd number of Nopes = action canceled
- Even number of Nopes = action proceeds

## Project Structure

```
exploding-kitten-bot-battle/
├── game/               # Core game engine and logic
│   ├── __init__.py
│   ├── cards.py       # Card types and Card class
│   ├── game_state.py  # GameState and CardCounts classes
│   ├── bot.py         # Base Bot class (inherit from this!)
│   ├── deck.py        # Deck management
│   └── game_engine.py # Main game loop and logic
├── bots/              # Bot implementations (add yours here!)
│   ├── __init__.py
│   ├── RandomBot.py   # Example: plays randomly
│   ├── CautiousBot.py # Example: plays defensively
│   └── AggressiveBot.py # Example: plays aggressively
├── tests/             # Automated tests
│   ├── __init__.py
│   └── test_game.py   # Unit tests for game components
├── main.py            # Entry point to run the game
└── README.md          # This file
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- No external dependencies required!

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zwazel/exploding-kitten-bot-battle.git
   cd exploding-kitten-bot-battle
   ```

2. Verify installation by running the tests:
   ```bash
   python3 -m unittest tests.test_game -v
   ```

## Creating Your Own Bot

To create your own bot, follow these steps:

1. **Create a new Python file** in the `bots` directory (e.g., `MyBot.py`).

2. **Import required classes**:
   ```python
   from typing import Optional, List
   from game import Bot, GameState, Card, CardType
   ```

3. **Inherit from the `Bot` class** and implement the required methods:

   ```python
   class MyBot(Bot):
       """My custom bot implementation."""

       def play(self, state: GameState) -> Optional[Card]:
           """
           Called when it's your turn to play a card.
           
           Args:
               state: Current game state (read-only)
               
           Returns:
               The card you want to play, or None to end play phase
           """
           # Your logic here
           return None

       def handle_exploding_kitten(self, state: GameState) -> int:
           """
           Called when you draw an Exploding Kitten and have a Defuse.
           
           Args:
               state: Current game state (read-only)
               
           Returns:
               Index where to insert the Exploding Kitten (0 = top)
           """
           # Your logic here
           return state.cards_left_to_draw  # Put it at the bottom

       def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
           """
           Called when you play a "See the Future" card.
           
           Args:
               state: Current game state (read-only)
               top_three: Top 3 cards of the deck (index 0 = top)
           """
           # Use this information for strategy
           pass
   ```

4. **Use the Bot API**:
   - `self.hand`: List of cards in your hand
   - `self.name`: Your bot's name
   - `self.has_card(card)`: Check if you have a specific card
   - `self.has_card_type(card_type)`: Check if you have any card of a type

### Example Bot

See `bots/CautiousBot.py` for a simple but effective bot that:
- Always uses "See the Future" when available
- Uses "Skip" when an Exploding Kitten was recently placed on top
- Puts Exploding Kittens at the bottom of the deck

## Running the Game

### Normal Mode

Run the game with all bots in the `bots` directory:

```bash
python3 main.py
```

The game will load all bots and run a complete game, showing each turn.

### Test Mode

Run in automatic test mode (no pauses, faster execution):

```bash
python3 main.py --test
```

Test mode features:
- Runs automatically without pauses
- If only 1 bot is found, it duplicates it to play against itself
- Requires at least 2 bots to run

## Running Tests

Run the automated test suite:

```bash
# Run all tests with verbose output
python3 -m unittest tests.test_game -v

# Run all tests in the tests directory
python3 -m unittest discover tests -v
```

The test suite includes:
- Card creation and manipulation
- Deck operations (draw, shuffle, insert)
- Bot behavior and hand management
- Game state management
- Complete game simulation

## Code Overview

### GameState

The `GameState` class contains all public information about the game:

- `total_cards_in_deck: CardCounts` - Original card counts in the deck
- `cards_left_to_draw: int` - Number of cards remaining in the deck
- `was_last_card_exploding_kitten: bool` - True if last drawn Exploding Kitten was returned to deck
- `history_of_played_cards: List[Card]` - All cards that have been played
- `alive_bots: int` - Number of bots still in the game

### Bot Base Class

All bots must inherit from `Bot` and implement:

1. `play(state: GameState) -> Optional[Card]`
   - Return a card to play, or `None` to end your turn
   - You can play multiple cards by returning one at a time
   - Return `None` to proceed to the draw phase

2. `handle_exploding_kitten(state: GameState) -> int`
   - Only called if you have a Defuse card
   - Return the position (0 to `cards_left_to_draw`) to insert the Exploding Kitten
   - Position 0 = top of deck, `cards_left_to_draw` = bottom

3. `see_the_future(state: GameState, top_three: List[Card]) -> None`
   - Called when you play a "See the Future" card
   - Use this information to inform your strategy

### Card Types (CardType Enum)

- `EXPLODING_KITTEN`
- `DEFUSE`
- `SKIP`
- `SEE_THE_FUTURE`
- `SHUFFLE`
- `ATTACK`
- `FAVOR`
- `NOPE`
- `CAT`

## Rules for Students

- **Do not modify** any code outside your own bot file in the `bots/` directory
- Your bot file must contain a class that inherits from `Bot`
- The class name should match the file name (e.g., `MyBot.py` contains `class MyBot(Bot)`)
- Your goal is to create the most competitive bot possible!
- Test your bot against the example bots to refine your strategy

## Tips for Success

1. **Use See the Future wisely** - Knowing what's coming helps you decide when to use Skip or Shuffle
2. **Manage your Defuse cards** - They're your lifeline!
3. **Track probabilities** - Use `state.history_of_played_cards` and `state.cards_left_to_draw` to calculate odds
4. **Be strategic with Exploding Kittens** - Where you place them affects other players
5. **Study the example bots** - They demonstrate different strategies

Good luck and have fun coding your bot! 🎮🐱💣