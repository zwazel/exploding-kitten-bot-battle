from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class FunghiBot(Bot):
  def __init__(self, name: str):
    super().__init__(name)
    self.future_cards = []


  def play(self, state: GameState):
    for card in self.hand:
      if card.card_type == CardType.NORMAL:
        return card

    played_defuse = 0
    played_skip = 0
    played_future_sight = 0
    played_normal = 0

    total_cards = (
        state.total_cards_in_deck.EXPLODING_KITTEN +
        state.total_cards_in_deck.DEFUSE +
        state.total_cards_in_deck.SKIP +
        state.total_cards_in_deck.SEE_THE_FUTURE +
        state.total_cards_in_deck.NORMAL
    )

    total_cards_left = state.cards_left_to_draw

    card_history = state.history_of_played_cards
    for card in card_history:
      if card.card_type == CardType.NORMAL:
        played_normal += 1
      if card.card_type == CardType.SKIP:
        played_skip += 1
      if card.card_type == CardType.DEFUSE:
        played_defuse += 1
      if card.card_type == CardType.SEE_THE_FUTURE:
        played_future_sight += 1

    ek_count =  state.alive_bots-1
    defuse_count = int(state.alive_bots/2 +.5)-played_defuse
    skip_count = state.alive_bots+6-played_skip
    future_sight_count = state.alive_bots*2-played_future_sight
    normal_count = state.alive_bots*6-played_normal

    possible_ek = ek_count/float(total_cards_left)
    possible_def = defuse_count/float(total_cards_left)
    possible_skip = skip_count/float(total_cards_left)
    possible_future_sight = future_sight_count/float(total_cards_left)
    possible_normal = normal_count/float(total_cards_left)

    defuse_in_hand = [card for card in self.hand if card.card_type == CardType.DEFUSE]

    print(f"{ek_count}/{float(total_cards_left)}")
    print(f"possible ek:{possible_ek} -----------------------------------------------------")
    if possible_ek >= .32 and not defuse_in_hand:
      see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
      skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
      if see_the_future_cards:
        return see_the_future_cards[0]
      elif CardType.EXPLODING_KITTEN in self.future_cards:
        if CardType.EXPLODING_KITTEN in self.future_cards[0]:
          print("avoided")
          return skip_cards[0]
        else:
          return None
      elif skip_cards:
        return skip_cards[0]

    if possible_ek == 0.16666666666666666:
      see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
      skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
      if see_the_future_cards:
        return see_the_future_cards[0]
      if CardType.EXPLODING_KITTEN in self.future_cards:
        if CardType.EXPLODING_KITTEN in self.future_cards[0]:
          print("avoided .16 --------")
          return skip_cards[0]
        else:
          return None

  def handle_exploding_kitten(self, state: GameState) -> int:
    return state.cards_left_to_draw

  def see_the_future(self, state: GameState, top_three: List[Card]):
    self.future_cards = top_three