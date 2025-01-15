import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class Stalinator(Bot):
    def __init__(self, name):
        print("Stalinator V3 - Simplified")
        super().__init__(name)
        self.risk = 0.0
        self.next_cards = []
        self.exploding_kitten_found = False

    def play(self, state: GameState) -> Optional[Card]:
        playable_cards = [card for card in self.hand if card.card_type == CardType.NORMAL]
        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]

        self.risk = max(0, self.risk - 0.1)

        if self.risk > 0.4 or len(self.hand) < 3:
            if see_the_future_cards:
                return see_the_future_cards[0]

        if self.risk > 0.7:
            if skip_cards:
                self.risk = 0.5
                return skip_cards[0]

        if self.exploding_kitten_found:
            if skip_cards:
                return skip_cards[0]
            self.exploding_kitten_found = False
            self.risk -= 0.2

        if playable_cards:
            if random.random() > 0.3:
                return random.choice(playable_cards)

        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        self.risk = 0.7
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        # Analyze the future cards
        self.next_cards = top_three
        self.exploding_kitten_found = any(card.card_type == CardType.EXPLODING_KITTEN for card in top_three)
