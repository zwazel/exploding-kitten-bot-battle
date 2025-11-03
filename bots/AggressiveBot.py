"""Example bot that plays aggressively."""

from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext


class AggressiveBot(Bot):
    """A bot that plays aggressively to pressure other players."""

    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """
        Play aggressively:
        - Use Attack cards to force others to take more turns
        - Use Shuffle to randomize the deck
        - Use See the Future to plan attacks
        - Use combos to steal cards
        """
        # Try 3-of-a-kind combos to steal specific cards
        from collections import Counter
        card_counts = Counter(c.card_type for c in self.hand)
        for card_type, count in card_counts.items():
            if count >= 3:
                cards = [c for c in self.hand if c.card_type == card_type][:3]
                return cards
        
        # Prefer Attack cards to pressure opponents
        for card in self.hand:
            if card.card_type == CardType.ATTACK:
                return card
        
        # Use Favor to take cards from others
        for card in self.hand:
            if card.card_type == CardType.FAVOR:
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
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        """Choose target with most cards, or strategically based on context."""
        if not alive_players:
            return None
        
        # For combos, target player with most cards
        if context in [TargetContext.TWO_OF_A_KIND, TargetContext.THREE_OF_A_KIND]:
            return max(alive_players, key=lambda b: len(b.hand))
        
        # For favor, target anyone (they choose what to give anyway)
        return alive_players[0]
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """Give away cat cards preferably."""
        cat_types = [CardType.TACOCAT, CardType.CATTERMELON, CardType.HAIRY_POTATO_CAT, 
                     CardType.BEARD_CAT, CardType.RAINBOW_RALPHING_CAT]
        for card in self.hand:
            if card.card_type in cat_types:
                return card
        # Give away anything except defuse
        for card in self.hand:
            if card.card_type != CardType.DEFUSE:
                return card
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """Request valuable cards."""
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """Choose most valuable card from discard."""
        priority = [CardType.DEFUSE, CardType.ATTACK, CardType.SEE_THE_FUTURE, CardType.SKIP]
        for card_type in priority:
            for card in discard_pile:
                if card.card_type == card_type:
                    return card
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        """Aggressively nope actions that benefit others."""
        # Nope combos and see the future
        if "combo" in action_description.lower() or "See the Future" in action_description:
            return True
        return False
