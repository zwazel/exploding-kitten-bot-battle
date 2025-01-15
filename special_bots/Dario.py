# bots/TimBot.py
import random
from typing import List, Optional

import deck
from bot import Bot
from bots.SmartBot import ProbabilityOfNextExploding
from card import Card, CardType
from game_handling.game_state import GameState


class dario(Bot):
  def play(self, state: GameState) -> Optional[Card]:
    if not self.hand:  # If hand is empty
      return None

    # Show available cards to the player
    print("Your cards:", [f"{i}: {card.card_type}" for i, card in enumerate(self.hand)])

    # Get player input
    choice = input("Choose a card to play (number) or press Enter to skip > ")

    # Skip turn if player presses Enter without a choice
    if not choice:
      return None

    try:
      # Convert input to integer index
      card_index = int(choice)

      # Check if index is valid
      if 0 <= card_index < len(self.hand):
        chosen_card = self.hand[card_index]
        # Don't allow playing DEFUSE cards
        if chosen_card.card_type != CardType.DEFUSE:
          return chosen_card
        else:
          print("Cannot play DEFUSE cards directly!")
          return None
      else:
        print("Invalid card number!")
        return None

    except ValueError:
      print("Please enter a valid number!")
      return None
  def handle_exploding_kitten(self, state: GameState) -> int:
    return random.randint(0, state.cards_left_to_draw)

  def see_the_future(self, state: GameState, top_three: List[Card]):
    self.probability_of_next_exploding = []
    for card in top_three:
      if card.card_type == CardType.EXPLODING_KITTEN:
        self.probability_of_next_exploding.append(ProbabilityOfNextExploding.DEFINITELY)
      else:
        self.probability_of_next_exploding.append(ProbabilityOfNextExploding.DEFINITELY_NOT)