from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class crazyBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards: List[Card] = []
        self.future = True

    def play(self, state: GameState) -> Optional[Card]:
        defuses = [card for card in self.hand if card.card_type == CardType.DEFUSE]

        normals = [card for card in self.hand if card.card_type == CardType.NORMAL]
        if normals:
            print("Eww a normal card!")
            return normals[0]

        skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
        if state.cards_left_to_draw <= 7 and len(skip_cards) >= 2:
            return skip_cards[0]
        if state.cards_left_to_draw <= 3 and len(skip_cards) >= 1:
            return skip_cards[0]
        if state.was_last_card_exploding_kitten and len(skip_cards) >= 2 or len(defuses) == 0:
            if skip_cards:
                return skip_cards[0]

        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        if see_the_future_cards and self.future:
            self.future = False
            return see_the_future_cards[0]

        if self.future_cards and self.future_cards[0].card_type == CardType.EXPLODING_KITTEN and self.future == False:
            if skip_cards:
                return skip_cards[0]

        if len(skip_cards) >= 3:
            self.future = True
            return skip_cards[0]


        self.future = True
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        defuses = [card for card in self.hand if card.card_type == CardType.DEFUSE]
        if len(defuses) >= 2:
            return 1
        return state.cards_left_to_draw


    def see_the_future(self, state: GameState, top_three: List[Card]):
        self.future_cards = top_three