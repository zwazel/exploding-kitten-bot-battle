import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState

"""
Winner of the first tournament!
"""

class AnthonyBotBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards: List[Card] = []


    def play(self, state: GameState) -> Optional[Card]:
        if self.future_cards:
            if self.future_cards[0].card_type == CardType.EXPLODING_KITTEN:
                skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
                if skip_cards:
                    return skip_cards[0]


        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        if see_the_future_cards:
            return see_the_future_cards[0]

        if random.random() < 0.5:
            return None
        playable_cards = [card for card in self.hand if card.card_type != CardType.DEFUSE]
        if playable_cards:
            return random.choice(playable_cards)
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        return random.randint(0, 1)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        self.future_cards = top_three