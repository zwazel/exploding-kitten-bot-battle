# exploding-kitten-bot-battle

## Project Overview

This project is a simplified version of the popular card game "Exploding Kittens". The goal is to create a bot that can play the game autonomously. Each bot will compete against bots created by other students. The game logic and rules are already implemented, and your task is to write the logic for your bot.

## Game Rules

- Each player (bot) starts with a hand of cards.
- Players take turns drawing cards from the deck.
- If a player draws an Exploding Kitten card, they must use a Defuse card to avoid exploding. If they cannot defuse, they are out of the game.
- Players can play various action cards to manipulate the game (e.g., Skip, See the Future).
- The last player remaining wins the game.

## Code Overview

### Bots

- Each bot has its own `hand` field, which is a list of cards that the bot has in its hand.
- Each bot gets the current `GameState` in each of its methods, so it can make decisions based on the current state of the game.
- The bot gets a name assigned. The name is just the file name minus the `.py` extension.

### GameState

The `GameState` class contains all the information about the current state of the game that is accessible to the bots. It's useful for the bots to make decisions based on the current state of the game.

- `total_cards_in_deck`: `CardCounts`
  - The amount of cards in the deck at the start of the game.
  - This is useful for calculating the probability of drawing a certain card.
- `cards_left_to_draw`: `int`
  - The amount of cards left in the draw pile.
  - This is useful for calculating the probability of drawing a certain card.
- `was_last_card_exploding_kitten`: `bool`
  - This is `True` if the last card drawn was an Exploding Kitten and was returned to the deck by the last player (they had a Defuse card and didn't explode).
  - This is `False` if the last card drawn was an Exploding Kitten and was not returned to the deck by the last player (they didn't have a Defuse card and exploded).
  - This is also `False` if the last card drawn was not an Exploding Kitten.
- `history_of_played_cards`: `list[Card]`
  - The history of the cards played.
  - Exploding Kitten cards are also added to this list if they were not returned to the deck (they're out of the game now, so, in a way, "played").
- `alive_bots`: `int`
  - The number of bots that are still alive.

## Creating Your Own Bot

To create your own bot, follow these steps:

1. **Create a new Python file** in the `bots` directory. Name the file after your bot (e.g., `MyBot.py`).

2. **Inherit from the `Bot` class** and implement the required methods:
   - `play(self, state: GameState) -> Optional[Card]`
     - This method is called when it's your turn to play.
     - You need to return the card you want to play, or `None` if you want to end your turn without playing anything.
   - `handle_exploding_kitten(self, state: GameState) -> int`
     - This method is called when you draw an Exploding Kitten card and have a Defuse card in your hand.
     - You need to return the index of the draw pile where you want to put the Exploding Kitten card back.
   - `see_the_future(self, state: GameState, top_three: List[Card])`
     - This method is called when you play a "See the Future" card.
     - You can see the top three cards of the draw pile.

## How to Run the Game

Run the game by starting the script without any flags. This will load all the bots in the `bots` folder and start the game. 
After each turn, you need to press enter to continue. This way you can see what each bot is doing at each turn.

```sh
python .\main.py
```

## How to Run the Game in Test Mode

Test the game by starting the script with the `--test` flag. This will duplicate the first bot loaded, if only 1 bot is loaded.
If you want your bot to be playing against itself, make sure that it's the only bot loaded.
Otherwise, if at least 2 bots are loaded, they are played against each other. The game will run automatically without any user input.

```sh
python .\main.py --test
```

## Rules for Students

- **Do not modify any code** other than your own bot file.
- Your goal is to write a bot that can play the game and compete against bots created by other students.
- Make sure your bot follows the game rules and implements the required methods correctly.

Good luck and have fun coding your bot!