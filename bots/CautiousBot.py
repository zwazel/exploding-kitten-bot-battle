"""Example bot that plays cautiously."""

from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType


class CautiousBot(Bot):
    """A bot that plays very cautiously."""

    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """
        Play cards cautiously:
        - Use See the Future if available
        - Use Skip if there's a good chance of drawing an Exploding Kitten
        - Avoid combos unless safe
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
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: str) -> Optional[Bot]:
        """Choose first available target."""
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """Give away the least valuable card (prefer cat cards)."""
        # Prefer giving cat cards
        cat_types = [CardType.TACOCAT, CardType.CATTERMELON, CardType.HAIRY_POTATO_CAT, 
                     CardType.BEARD_CAT, CardType.RAINBOW_RALPHING_CAT]
        for card in self.hand:
            if card.card_type in cat_types:
                return card
        # Otherwise give any non-defuse card
        for card in self.hand:
            if card.card_type != CardType.DEFUSE:
                return card
        # Last resort, give anything
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """Request Defuse if possible, otherwise See the Future."""
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """Choose Defuse from discard if available."""
        for card in discard_pile:
            if card.card_type == CardType.DEFUSE:
                return card
        for card in discard_pile:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        """Only nope attacks and favors against us."""
        # Cautious bot rarely nopes
        if "Attack" in action_description and "playing Attack" in action_description:
            return True  # Always nope attacks
        return False
