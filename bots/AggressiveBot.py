"""Example bot that plays aggressively."""

from typing import Optional, List, Union, Dict
from collections import Counter
from game import Bot, GameState, Card, CardType, TargetContext, GameAction, ActionType


class AggressiveBot(Bot):
    """
    A bot that plays aggressively to pressure other players.
    
    Strategy:
    - Prioritizes 3-of-a-kind and 2-of-a-kind combos to steal cards
    - Uses Attack cards to force opponents to take extra turns
    - Places Exploding Kittens near the top to threaten opponents
    - Uses Favor to steal cards
    - Targets players with most cards
    - Aggressively nopes combos and valuable actions
    - Tracks opponent card counts and behaviors
    """
    
    def __init__(self, name: str):
        """Initialize the aggressive bot with tracking variables."""
        super().__init__(name)
        self.opponent_defuse_count: Dict[str, int] = {}  # Track estimated defuses
        self.seen_future_cards: List[Card] = []  # Cards seen from See the Future
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """
        Play aggressively:
        - Prioritize 3-of-a-kind combos to request specific valuable cards
        - Use 2-of-a-kind combos to randomly steal cards
        - Use Attack cards to pressure opponents
        - Use Favor to take cards from others
        - Use See the Future to plan aggressive moves
        - Use Shuffle when it benefits us
        """
        # Try 3-of-a-kind combos first - most powerful for stealing specific cards
        combo = self._try_three_of_a_kind()
        if combo:
            return combo
        
        # Try 2-of-a-kind combos - good for stealing random cards
        combo = self._try_two_of_a_kind()
        if combo:
            return combo
        
        # Use Attack cards to pressure opponents with extra turns
        for card in self.hand:
            if card.card_type == CardType.ATTACK:
                return card
        
        # Use Favor to take cards from others
        for card in self.hand:
            if card.card_type == CardType.FAVOR:
                return card
        
        # Use See the Future to plan our next moves
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        
        # Check if we should shuffle based on what we know
        if self._should_shuffle(state):
            for card in self.hand:
                if card.card_type == CardType.SHUFFLE:
                    return card
        
        # Use Shuffle to randomize when many players are still alive
        if state.alive_bots > 2:
            for card in self.hand:
                if card.card_type == CardType.SHUFFLE:
                    return card
        
        # Don't play more cards - end turn
        return None
    
    def _try_three_of_a_kind(self) -> Optional[List[Card]]:
        """
        Try to form a 3-of-a-kind combo.
        
        Returns:
            List of 3 cards for combo, or None if not possible
        """
        card_counts = Counter(c.card_type for c in self.hand)
        
        # Try to find 3-of-a-kind (excluding Defuse and Exploding Kitten)
        for card_type, count in card_counts.items():
            if count >= 3 and card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]:
                cards = [c for c in self.hand if c.card_type == card_type][:3]
                return cards
        
        return None
    
    def _try_two_of_a_kind(self) -> Optional[List[Card]]:
        """
        Try to form a 2-of-a-kind combo.
        
        Prioritizes cat cards to preserve action cards.
        
        Returns:
            List of 2 cards for combo, or None if not possible
        """
        card_counts = Counter(c.card_type for c in self.hand)
        
        # Prefer using cat cards for 2-of-a-kind to preserve action cards
        cat_types = [CardType.TACOCAT, CardType.CATTERMELON, CardType.HAIRY_POTATO_CAT,
                     CardType.BEARD_CAT, CardType.RAINBOW_RALPHING_CAT]
        
        for cat_type in cat_types:
            if card_counts.get(cat_type, 0) >= 2:
                cards = [c for c in self.hand if c.card_type == cat_type][:2]
                return cards
        
        # If no cat combos, use other cards (except Defuse and Exploding Kitten)
        for card_type, count in card_counts.items():
            if count >= 2 and card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]:
                cards = [c for c in self.hand if c.card_type == card_type][:2]
                return cards
        
        return None
    
    def _should_shuffle(self, state: GameState) -> bool:
        """
        Decide if we should shuffle based on known information.
        
        Args:
            state: Current game state
            
        Returns:
            True if we should shuffle, False otherwise
        """
        # Shuffle if we saw an Exploding Kitten in the top 3 cards
        if self.seen_future_cards:
            for card in self.seen_future_cards:
                if card.card_type == CardType.EXPLODING_KITTEN:
                    return True
        
        # Don't shuffle otherwise - it might help opponents
        return False

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Aggressively put the Exploding Kitten near the top to threaten next player.
        
        Strategy: Place it 1-2 cards down so it's threatening but not guaranteed.
        This pressures the next player without being too obvious.
        
        Args:
            state: Current game state
            
        Returns:
            Position near top of deck (1-2 cards down)
        """
        # Place it 1-2 cards down from the top to threaten opponents
        # but not make it too obvious/guaranteed
        if state.cards_left_to_draw == 0:
            return 0
        return min(2, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Use this information to plan aggressive strategy.
        
        Args:
            state: Current game state
            top_three: Top 3 cards of the deck
        """
        # Store what we see for strategic decisions
        self.seen_future_cards = top_three.copy()
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        """
        Aggressively choose targets with most cards.
        
        Strategy:
        - For combos: target player with most cards (better chance of getting what we want)
        - For favor: target player with most cards (more options to choose from)
        
        Args:
            state: Current game state
            alive_players: List of bots that can be targeted
            context: Why we're choosing a target
            
        Returns:
            Target bot, or None if no players available
        """
        if not alive_players:
            return None
        
        # Always target player with most cards - they likely have good cards
        return max(alive_players, key=lambda b: len(b.hand))
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """
        Give away least valuable cards when forced to.
        
        Priority (from least to most valuable):
        1. Cat cards (only good for combos)
        2. Nope (we're aggressive, not defensive)
        3. Other action cards
        4. Defuse (never give this away if possible)
        
        Args:
            state: Current game state
            
        Returns:
            Card to give away
        """
        # Prefer giving cat cards
        cat_types = [CardType.TACOCAT, CardType.CATTERMELON, CardType.HAIRY_POTATO_CAT, 
                     CardType.BEARD_CAT, CardType.RAINBOW_RALPHING_CAT]
        for card in self.hand:
            if card.card_type in cat_types:
                return card
        
        # Give away Nope next (we're aggressive, not defensive)
        for card in self.hand:
            if card.card_type == CardType.NOPE:
                return card
        
        # Give away Shuffle or See the Future
        for card in self.hand:
            if card.card_type in [CardType.SHUFFLE, CardType.SEE_THE_FUTURE]:
                return card
        
        # Give away Favor
        for card in self.hand:
            if card.card_type == CardType.FAVOR:
                return card
        
        # Keep Attack and Skip if possible
        # Give away anything except Defuse
        for card in self.hand:
            if card.card_type != CardType.DEFUSE:
                return card
        
        # Absolute last resort
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """
        Request most valuable cards for 3-of-a-kind combo.
        
        Priority:
        1. Defuse (survival and can trade)
        2. Attack (aggressive pressure)
        3. Skip (safety)
        
        Args:
            state: Current game state
            
        Returns:
            Card type to request
        """
        # Always request Defuse - most valuable card
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """
        Choose most valuable card from discard for 5-unique combo.
        
        Priority:
        1. Defuse (survival)
        2. Attack (aggression)
        3. See the Future (information for planning)
        4. Skip (safety)
        
        Args:
            state: Current game state
            discard_pile: Cards available in discard pile
            
        Returns:
            Card to take from discard
        """
        # Priority order for aggressive play
        priority = [CardType.DEFUSE, CardType.ATTACK, CardType.SEE_THE_FUTURE, 
                   CardType.SKIP, CardType.FAVOR, CardType.NOPE]
        
        for card_type in priority:
            for card in discard_pile:
                if card.card_type == card_type:
                    return card
        
        # Take any card if priority cards not available
        return discard_pile[0] if discard_pile else None
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        """
        Track opponent actions to inform aggressive strategy.
        
        Tracks:
        - When opponents use Defuse (they have fewer defenses)
        - When cards are drawn (deck state changes)
        - When Exploding Kittens are placed back
        
        Args:
            state: Current game state
            action: The action that occurred
            actor: Bot who performed the action
        """
        # Track when opponents use Defuse cards
        if action.action_type == ActionType.DEFUSE:
            if actor.name not in self.opponent_defuse_count:
                self.opponent_defuse_count[actor.name] = 1
            else:
                self.opponent_defuse_count[actor.name] += 1
        
        # Reset seen cards when deck is shuffled
        if action.action_type == ActionType.CARD_PLAY and action.card == CardType.SHUFFLE:
            self.seen_future_cards = []
        
        # Update seen cards when someone draws
        if action.action_type == ActionType.CARD_DRAW and self.seen_future_cards:
            if len(self.seen_future_cards) > 0:
                self.seen_future_cards.pop(0)
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        """
        Aggressively nope actions that benefit opponents.
        
        Will nope:
        - Any combos (they're stealing/taking cards)
        - See the Future (information is power)
        - Favors (unless targeting us - then let them have a bad card)
        
        Args:
            state: Current game state
            action: The action being played
            
        Returns:
            True to play Nope, False otherwise
        """
        # Don't nope if we don't have a Nope card
        if not self.has_card_type(CardType.NOPE):
            return False
        
        # Always nope combos - they're stealing cards
        if action.action_type == ActionType.COMBO_PLAY:
            # But if it's targeting someone else, let it happen (weakens them)
            if action.target and action.target != self.name:
                return False
            return True
        
        # Nope See the Future - information is valuable
        if action.action_type == ActionType.CARD_PLAY and action.card == CardType.SEE_THE_FUTURE:
            return True
        
        # Don't nope Attacks - let them pressure other players
        # (We can handle extra draws better than defensive bots)
        
        # Don't nope Favors targeting us - we'll just give them a cat card
        
        return False
