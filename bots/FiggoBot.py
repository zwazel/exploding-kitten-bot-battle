import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class FiggoBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards: List[Card] = []

    def play(self, state: GameState) -> Optional[Card]:
        exploding_kitten_cards = [card for card in self.hand if card.card_type == CardType.EXPLODING_KITTEN]
        if exploding_kitten_cards:
            return exploding_kitten_cards[0]

        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        if see_the_future_cards:
            return see_the_future_cards[0]

        if self._is_exploding_kitten_likely(state):
            skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
            if skip_cards:
                return skip_cards[0]
        normal_cards = [card for card in self.hand if card.card_type == CardType.NORMAL]
        if normal_cards:
            return random.choice(normal_cards)
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0

    def see_the_future(self, state: GameState, top_three: List[Card]):
        self.future_cards = top_three
        if any(card.card_type == CardType.EXPLODING_KITTEN for card in top_three):
            print(f"Exploding Kitten voraus! Manipulation wird vorbereitet.")

    def _is_exploding_kitten_likely(self, state: GameState) -> bool:
        exploding_kittens_left = state.alive_bots - 1
        probability = exploding_kittens_left / state.cards_left_to_draw
        return probability > 0.3
