# exploding-kitten-bot-battle

Test the game by starting the script with the --test flag.
This will duplicate the first bot loaded. If you want your bot to be playing against himself, make sure that it's the only bot loaded.

## Code Overview

### Bots
- Each bot has its own "Hand" field, which is a list of cards that the bot has in its hand.
- Each bot gets the current GameState in each of its methods, so it can make decisions based on the current state of the game.

### GameState
- total_cards_in_deck: CardCounts
  - the amount of cards in the deck at the start of the game
  - With this you can see all the Types of Cards and how many of them exist in the start of the deck
  - For example, This is useful for calculating the probability of drawing a certain card
- cards_left_to_draw: int
  - the amount of cards left in the draw pile
  - For example, this is useful for calculating the probability of drawing a certain card
- was_last_card_exploding_kitten: bool
  - This is TRUE if the last card drawn was an exploding kitten and was RETURNED to the deck by the last player (he had a defuse card and didn't explode). 
  - This is FALSE if the last card drawn was an exploding kitten and was NOT RETURNED to the deck by the last player (he didn't have a defuse card and exploded). 
  - This is also FALSE if the last card drawn was NOT an exploding kitten, but anything else.
- history_of_played_cards: list[Card]
  - the history of the cards played
  - exploding kitten cards are also added to this list, if they were NOT returned to the deck / a player exploded and couldn't defuse it (they're out of the game now, so, in a way, "played")
- alive_bots: int
  - the amount of bots that are still alive

## Creating your own Bot
Have a look at the "TimBot.py" file to see an example of a bot implementation.

You need to create a class that inherits from the Bot class and implement the following methods:
- play(self, state: GameState) -> Optional[Card]
  - This method is called when it's your turn to play
  - You need to return the card you want to play, or None if you want to end your turn without playing anything
- handle_exploding_kitten(self, state: GameState) -> int
  - This method is called when you draw an exploding kitten card and had a defuse card in your hand
  - As you're still alive, you need to put the exploding kitten card back into your hand
  - You can choose where to put it back, so you need to return the index of the draw pile in which you want to put the card in
- see_the_future(self, state: GameState, top_three: List[Card])
  - This method is called when you play a "See the future" card
  - You can see the top three cards of the draw pile


## How to run the game
python .\main.py
 
## How to run the game in test mode
python .\main.py --test

