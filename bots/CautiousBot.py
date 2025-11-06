"""Example bot that plays cautiously."""

from typing import Optional, List, Union
from collections import Counter
from game import Bot, GameState, Card, CardType, TargetContext, GameAction, ActionType


class CautiousBot(Bot):
    """
    A bot that plays very cautiously and defensively.
    
    Strategy:
    - Always uses See the Future to gather information
    - Calculates explosion risk probability
    - Uses Skip when danger is high
    - Puts Exploding Kittens at the bottom
    - Uses 2-of-a-kind combos defensively to get cards
    - Nopes attacks against self
    - Tracks what cards have been seen
    """
    
    def __init__(self, name: str):
        """Initialize the cautious bot with tracking variables."""
        super().__init__(name)
        self.seen_future_cards: List[Card] = []  # Cards seen from See the Future
        self.known_top_position: int = 0  # How many cards from top we know about
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """
        Play cards cautiously:
        - Always use See the Future to gather intel
        - Use Skip if high explosion risk or known danger ahead
        - Use Shuffle if an Exploding Kitten is near the top
        - Use 2-of-a-kind combos defensively to steal cards
        - Use 3-of-a-kind combos to request valuable cards (but cautiously)
        """
        # Always use See the Future if we have it - information is key
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        
        # Check if we know an Exploding Kitten is on top
        if self.seen_future_cards and len(self.seen_future_cards) > 0:
            if self.seen_future_cards[0].card_type == CardType.EXPLODING_KITTEN:
                # Top card is Exploding Kitten! Use Skip if we have it
                for card in self.hand:
                    if card.card_type == CardType.SKIP:
                        self.seen_future_cards.pop(0)  # Remove known top card
                        return card
                
                # If no Skip, try to Shuffle the deck
                for card in self.hand:
                    if card.card_type == CardType.SHUFFLE:
                        self.seen_future_cards = []  # Reset knowledge after shuffle
                        return card
        
        # If Exploding Kitten was just placed back on top, use Skip
        if state.was_last_card_exploding_kitten:
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card
        
        # Calculate explosion risk
        risk = self._calculate_explosion_risk(state)
        
        # If risk is very high (>40%), use Skip
        if risk > 0.4:
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card
        
        # Try 3-of-a-kind combo to request valuable cards (but cautiously)
        # Only when we have many cards to spare
        if len(self.hand) >= 6:
            combo = self._try_three_of_a_kind_combo()
            if combo:
                return combo
        
        # Try defensive 2-of-a-kind combo to steal cards from others
        # Use when we have enough cards or in late game
        if len(self.hand) >= 5 or state.alive_bots <= 2:
            combo = self._try_two_of_a_kind_combo()
            if combo:
                return combo
        
        # Don't play other cards unnecessarily - be cautious
        return None
    
    def _try_three_of_a_kind_combo(self) -> Optional[List[Card]]:
        """
        Try to form a 3-of-a-kind combo (cautiously).
        
        Never uses DEFUSE or EXPLODING_KITTEN cards in combos.
        
        Returns:
            List of 3 cards for combo, or None if not possible
        """
        card_types = Counter(c.card_type for c in self.hand)
        
        # Find 3-of-a-kind (excluding DEFUSE and EXPLODING_KITTEN)
        for card_type, count in card_types.items():
            if count >= 3 and card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]:
                cards = [c for c in self.hand if c.card_type == card_type][:3]
                return cards
        
        return None
    
    def _try_two_of_a_kind_combo(self) -> Optional[List[Card]]:
        """
        Try to form a 2-of-a-kind combo (defensively).
        
        Prefers cat cards to preserve action cards.
        Never uses DEFUSE or EXPLODING_KITTEN cards in combos.
        
        Returns:
            List of 2 cards for combo, or None if not possible
        """
        card_types = Counter(c.card_type for c in self.hand)
        
        # Prefer cat cards for combos
        cat_types = [CardType.TACOCAT, CardType.CATTERMELON, CardType.HAIRY_POTATO_CAT,
                     CardType.BEARD_CAT, CardType.RAINBOW_RALPHING_CAT]
        
        for cat_type in cat_types:
            if card_types.get(cat_type, 0) >= 2:
                cards = [c for c in self.hand if c.card_type == cat_type][:2]
                return cards
        
        # If no cat combos, try other cards (but not Defuse or Exploding Kitten)
        for card_type, count in card_types.items():
            if count >= 2 and card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]:
                cards = [c for c in self.hand if c.card_type == card_type][:2]
                return cards
        
        return None
    
    def _calculate_explosion_risk(self, state: GameState) -> float:
        """
        Calculate the probability of drawing an Exploding Kitten.
        
        Args:
            state: Current game state
            
        Returns:
            Probability between 0.0 and 1.0
        """
        if state.cards_left_to_draw == 0:
            return 0.0
        
        # Count how many Exploding Kittens are likely in the deck
        # We know from game setup there are (number of players - 1) Exploding Kittens
        total_kittens = state.alive_bots  # This is an approximation
        
        # Count how many have been seen/played
        played_kittens = sum(
            1 for card in state.history_of_played_cards 
            if card.card_type == CardType.EXPLODING_KITTEN
        )
        
        remaining_kittens = max(0, total_kittens - played_kittens - 1)  # -1 for current round
        
        # Probability = remaining kittens / cards left
        return min(1.0, remaining_kittens / state.cards_left_to_draw)

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Always put the Exploding Kitten at the bottom of the deck for safety.
        
        Args:
            state: Current game state
            
        Returns:
            Bottom position of the deck
        """
        return state.cards_left_to_draw  # Bottom of deck - safest option

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Remember what we saw for strategic planning.
        
        This information is crucial for the cautious bot's decision making.
        
        Args:
            state: Current game state
            top_three: Top 3 cards we can see (index 0 = top card)
        """
        # Store the cards we saw
        self.seen_future_cards = top_three.copy()
        self.known_top_position = len(top_three)
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        """
        Choose target strategically based on context.
        
        For combos: target player with most cards (more chance of getting what we want)
        For favor: target anyone (they choose what to give)
        
        Args:
            state: Current game state
            alive_players: List of bots that can be targeted
            context: Why we're choosing a target
            
        Returns:
            Selected target bot, or None if no players available
        """
        if not alive_players:
            return None
        
        # For combos, target player with most cards
        if context in [TargetContext.TWO_OF_A_KIND, TargetContext.THREE_OF_A_KIND]:
            return max(alive_players, key=lambda b: len(b.hand))
        
        # For favor, just choose first available
        return alive_players[0]
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """
        Give away the least valuable card.
        
        Priority (from least to most valuable):
        1. Cat cards (for combos only)
        2. Other action cards
        3. Defuse (never give this away if possible)
        
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
        
        # Give away Nope cards next (we're cautious, not aggressive with nopes)
        for card in self.hand:
            if card.card_type == CardType.NOPE:
                return card
        
        # Give away Shuffle or Favor
        for card in self.hand:
            if card.card_type in [CardType.SHUFFLE, CardType.FAVOR]:
                return card
        
        # Give away other action cards except Defuse, Skip, and See the Future
        for card in self.hand:
            if card.card_type not in [CardType.DEFUSE, CardType.SKIP, CardType.SEE_THE_FUTURE]:
                return card
        
        # Last resort - give Skip
        for card in self.hand:
            if card.card_type == CardType.SKIP:
                return card
        
        # Absolute last resort - give anything
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """
        Request most valuable card type for 3-of-a-kind combo.
        
        Priority:
        1. Defuse (survival)
        2. Skip (safety)
        3. See the Future (information)
        
        Args:
            state: Current game state
            
        Returns:
            Card type to request
        """
        # Always request Defuse first - it's the most valuable for survival
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """
        Choose most valuable card from discard pile for 5-unique combo.
        
        Priority:
        1. Defuse (survival)
        2. Skip (safety)
        3. See the Future (information)
        
        Args:
            state: Current game state
            discard_pile: Cards available in discard pile
            
        Returns:
            Card to take from discard
        """
        # Priority order for taking from discard
        priority = [CardType.DEFUSE, CardType.SKIP, CardType.SEE_THE_FUTURE, 
                   CardType.SHUFFLE, CardType.NOPE, CardType.ATTACK]
        
        for card_type in priority:
            for card in discard_pile:
                if card.card_type == card_type:
                    return card
        
        # If none of the priority cards, take any
        return discard_pile[0] if discard_pile else None
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        """
        Track important actions for cautious decision-making.
        
        Args:
            state: Current game state
            action: The action that occurred
            actor: Bot who performed the action
        """
        # Update our knowledge when cards are drawn
        if action.action_type == ActionType.CARD_DRAW and self.seen_future_cards:
            # Someone drew a card, update our known future
            if len(self.seen_future_cards) > 0:
                self.seen_future_cards.pop(0)
        
        # Reset knowledge when deck is shuffled
        if (action.action_type == ActionType.CARD_PLAY and 
            action.card is not None and action.card == CardType.SHUFFLE):
            self.seen_future_cards = []
            self.known_top_position = 0
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        """
        Nope only the most threatening actions.
        
        Will nope:
        - Attacks (always - they make us draw more)
        - Favors targeting us
        - Combos targeting us
        
        Args:
            state: Current game state
            action: The action being played
            
        Returns:
            True to play Nope, False otherwise
        """
        # Don't nope if we don't have a Nope card
        if not self.has_card_type(CardType.NOPE):
            return False
        
        # Always nope attacks - they force extra draws which is risky
        if action.action_type == ActionType.CARD_PLAY and action.card == CardType.ATTACK:
            return True
        
        # Nope favors and combos that target us
        if action.target == self.name:
            if action.action_type == ActionType.CARD_PLAY and action.card == CardType.FAVOR:
                return True
            if action.action_type == ActionType.COMBO_PLAY:
                return True
        
        # Don't nope other actions - be cautious with our Nope cards
        return False
