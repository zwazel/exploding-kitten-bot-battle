import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class TimBot(Bot):
    def play(self, state: GameState) -> Optional[Card]:
        if random.random() < 0.5:
            return None
        playable_cards = [card for card in self.hand if card.card_type != CardType.DEFUSE]
        if playable_cards:
            return random.choice(playable_cards)
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        pass
