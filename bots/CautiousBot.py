"""Example bot that plays cautiously."""

from typing import Optional, List
from game import Bot, GameState, Card, CardType


class CautiousBot(Bot):
    """A bot that plays very cautiously."""

    def play(self, state: GameState) -> Optional[Card]:
        """
        Play cards cautiously:
        - Use See the Future if available
        - Use Skip if there's a good chance of drawing an Exploding Kitten
        """
        # Always use See the Future if we have it
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        
        # If we recently saw an Exploding Kitten was put back, use Skip
        if state.was_last_card_exploding_kitten:
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card
        
        # Don't play other cards unnecessarily
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """Put the Exploding Kitten at the bottom of the deck."""
        return state.cards_left_to_draw  # Bottom of deck

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """Remember what we saw (cautious bot uses this info in play method)."""
        # In a real implementation, we might store this information
        pass
