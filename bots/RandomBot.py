"""Example bot that plays randomly."""

import random
from typing import Optional, List
from game import Bot, GameState, Card, CardType


class RandomBot(Bot):
    """A bot that makes random decisions."""

    def play(self, state: GameState) -> Optional[Card]:
        """Randomly decide whether to play a card."""
        playable_cards = [
            card for card in self.hand 
            if card.card_type in [CardType.SKIP, CardType.SEE_THE_FUTURE, 
                                  CardType.SHUFFLE, CardType.ATTACK]
        ]
        
        if playable_cards and random.random() < 0.3:  # 30% chance to play a card
            return random.choice(playable_cards)
        
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """Put the Exploding Kitten at a random position."""
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """Just observe the cards (random bot doesn't use this info)."""
        pass
