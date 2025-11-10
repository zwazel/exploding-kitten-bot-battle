"""Example bot that plays randomly."""

import random
from typing import Optional, List, Union
from collections import Counter
from game import Bot, GameState, Card, CardType, TargetContext, GameAction, ActionType


class RandomBot(Bot):
    """
    A bot that makes completely random decisions.
    
    This bot will:
    - Randomly decide whether to play cards, combos, or nothing
    - Randomly decide whether to nope actions
    - Randomly place Exploding Kittens
    - Make random choices for all required actions
    """

    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """
        Randomly decide whether to play a card or combo.
        
        The bot will continue playing cards randomly until it decides to stop,
        then draw a card (ending the turn).
        """
        # 50% chance to try playing something
        if random.random() < 0.5:
            # 30% chance to try a combo if available
            if random.random() < 0.3:
                combo = self._try_random_combo()
                if combo:
                    return combo
            
            # Try playing a single card
            playable_cards = [
                card for card in self.hand 
                if card.card_type in [CardType.SKIP, CardType.SEE_THE_FUTURE, 
                                      CardType.SHUFFLE, CardType.ATTACK, CardType.FAVOR, CardType.NOPE]
            ]
            
            if playable_cards and random.random() < 0.5:
                return random.choice(playable_cards)
        
        # 50% of the time (or if no playable cards), return None to end play phase
        return None
    
    def _try_random_combo(self) -> Optional[List[Card]]:
        """
        Try to form a random combo from hand.
        
        Randomly tries to form 2-of-a-kind, 3-of-a-kind, or 5-unique combos.
        Returns None if no combo is possible or randomly decides not to play one.
        """
        card_types = Counter(c.card_type for c in self.hand)
        
        # Collect all possible combos
        possible_combos = []
        
        # Find 2-of-a-kind combos
        for card_type, count in card_types.items():
            if count >= 2 and card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]:
                cards = [c for c in self.hand if c.card_type == card_type][:2]
                possible_combos.append(cards)
        
        # Find 3-of-a-kind combos
        for card_type, count in card_types.items():
            if count >= 3 and card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]:
                cards = [c for c in self.hand if c.card_type == card_type][:3]
                possible_combos.append(cards)
        
        # Find 5-unique combo
        if len(self.hand) >= 5:
            unique_types = [ct for ct in card_types.keys() 
                          if ct not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]]
            if len(unique_types) >= 5:
                cards = []
                used_types = set()
                for card in self.hand:
                    if (card.card_type not in used_types and 
                        card.card_type not in [CardType.DEFUSE, CardType.EXPLODING_KITTEN]):
                        cards.append(card)
                        used_types.add(card.card_type)
                        if len(cards) == 5:
                            possible_combos.append(cards)
                            break
        
        # Randomly pick one combo or return None
        if possible_combos and random.random() < 0.5:
            return random.choice(possible_combos)
        
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Randomly put the Exploding Kitten at any position in the deck.
        
        Args:
            state: Current game state
            
        Returns:
            Random position from 0 (top) to cards_left_to_draw (bottom)
        """
        # Ensure we have at least one position available
        if state.cards_left_to_draw == 0:
            return 0
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Observe the top 3 cards (random bot doesn't use this information).
        
        Args:
            state: Current game state
            top_three: Top 3 cards of the deck
        """
        # Random bot doesn't track or use this information
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        """
        Randomly choose a target from available players.
        
        Args:
            state: Current game state
            alive_players: List of bots that can be targeted
            context: Why a target is being chosen
            
        Returns:
            Randomly selected bot from alive_players, or None if no players available
        """
        return random.choice(alive_players) if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """
        Randomly choose a card to give away (for Favor or combo request).
        
        Args:
            state: Current game state
            
        Returns:
            Randomly selected card from hand, or None if hand is empty
        """
        return random.choice(self.hand) if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """
        Randomly choose a card type to request (for 3-of-a-kind combo).
        
        Args:
            state: Current game state
            
        Returns:
            Randomly selected card type from common valuable types
        """
        # List of valuable card types to request
        types = [
            CardType.DEFUSE, CardType.SKIP, CardType.ATTACK, 
            CardType.SEE_THE_FUTURE, CardType.SHUFFLE, CardType.FAVOR,
            CardType.NOPE, CardType.TACOCAT, CardType.CATTERMELON
        ]
        return random.choice(types)
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """
        Randomly choose a card from the discard pile (for 5-unique combo).
        
        Args:
            state: Current game state
            discard_pile: Cards available in the discard pile
            
        Returns:
            Randomly selected card from discard pile, or None if empty
        """
        return random.choice(discard_pile) if discard_pile else None
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        """
        Called when any action occurs (random bot doesn't track actions).
        
        Args:
            state: Current game state
            action: The action that was played
            actor: The bot who played the action
        """
        # Random bot doesn't track or learn from actions
        pass
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        """
        Randomly decide whether to nope an action.
        
        The bot will nope with 25% probability if it has a Nope card.
        
        Args:
            state: Current game state
            action: The action being played that can be noped
            
        Returns:
            True to play Nope (25% chance), False otherwise
        """
        # Only nope if we have a nope card (game engine will check this too)
        # 25% chance to randomly nope any action
        return self.has_card_type(CardType.NOPE) and random.random() < 0.25
