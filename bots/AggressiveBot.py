"""Example bot that plays aggressively."""

from typing import Optional, List
from game import Bot, GameState, Card, CardType


class AggressiveBot(Bot):
    """A bot that plays aggressively to pressure other players."""

    def play(self, state: GameState) -> Optional[Card]:
        """
        Play aggressively:
        - Use Attack cards to force others to take more turns
        - Use Shuffle to randomize the deck
        - Use See the Future to plan attacks
        """
        # Prefer Attack cards to pressure opponents
        for card in self.hand:
            if card.card_type == CardType.ATTACK:
                return card
        
        # Use Shuffle to randomize when many players are still alive
        if state.alive_bots > 2:
            for card in self.hand:
                if card.card_type == CardType.SHUFFLE:
                    return card
        
        # Use See the Future to plan
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """Put the Exploding Kitten near the top to threaten the next player."""
        # Place it 1-2 cards down so it's threatening but not guaranteed
        return min(2, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """Use this information to decide strategy."""
        pass
