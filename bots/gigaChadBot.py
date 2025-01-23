from inspect import stack
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class ImprovedRandomBot(Bot):
    one_next_card = None
    two_next_card = None
    three_next_card = None

    explosive_kitten_cards = 0

    def play(self, state: GameState) -> Optional[Card]:
        """
        Strategic card play to maximize survival
        """
        playable_cards = [card for card in self.hand if card.card_type != CardType.DEFUSE]

        self.explosive_kitten_cards = state.alive_bots - 1

        chance_to_be_explosive_kitten = self.explosive_kitten_cards / state.cards_left_to_draw

        if chance_to_be_explosive_kitten > 25:
            if CardType.SKIP in playable_cards:
                return Card(CardType.SKIP)


        if Card(CardType.SEE_THE_FUTURE) in playable_cards:
            return Card(CardType.SEE_THE_FUTURE)

        if (self.one_next_card == CardType.EXPLODING_KITTEN or
            state.was_last_card_exploding_kitten):
            if Card(CardType.SKIP) in playable_cards:
                return Card(CardType.SKIP)

        if CardType.NORMAL in playable_cards:
            return Card(CardType.NORMAL)

        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Strategic exploding kitten placement
        """
        return 0

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Carefully track upcoming cards
        """
        self.one_next_card = top_three[0].card_type if top_three else None
        self.two_next_card = top_three[1].card_type if len(top_three) > 1 else None
        self.three_next_card = top_three[2].card_type if len(top_three) > 2 else None