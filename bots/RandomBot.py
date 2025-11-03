"""Example bot that plays randomly."""

import random
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext, GameAction, ActionType


# Probability of playing a card when available
PLAY_CARD_PROBABILITY = 0.3


class RandomBot(Bot):
    """A bot that makes random decisions."""

    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """Randomly decide whether to play a card or combo."""
        # Sometimes try combos
        if random.random() < 0.1:  # 10% chance to try combo
            combo = self._try_random_combo()
            if combo:
                return combo
        
        # Play single cards
        playable_cards = [
            card for card in self.hand 
            if card.card_type in [CardType.SKIP, CardType.SEE_THE_FUTURE, 
                                  CardType.SHUFFLE, CardType.ATTACK, CardType.FAVOR]
        ]
        
        if playable_cards and random.random() < PLAY_CARD_PROBABILITY:
            return random.choice(playable_cards)
        
        return None
    
    def _try_random_combo(self) -> Optional[List[Card]]:
        """Try to form a random combo from hand."""
        from collections import Counter
        card_types = Counter(c.card_type for c in self.hand)
        
        # Try 2-of-a-kind
        for card_type, count in card_types.items():
            if count >= 2:
                cards = [c for c in self.hand if c.card_type == card_type][:2]
                if random.random() < 0.5:
                    return cards
        
        # Try 3-of-a-kind
        for card_type, count in card_types.items():
            if count >= 3:
                cards = [c for c in self.hand if c.card_type == card_type][:3]
                if random.random() < 0.5:
                    return cards
        
        # Try 5-unique
        if len(self.hand) >= 5:
            unique_types = list(set(c.card_type for c in self.hand))
            if len(unique_types) >= 5:
                cards = []
                used_types = set()
                for card in self.hand:
                    if card.card_type not in used_types:
                        cards.append(card)
                        used_types.add(card.card_type)
                        if len(cards) == 5:
                            return cards if random.random() < 0.3 else None
        
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """Put the Exploding Kitten at a random position."""
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """Just observe the cards (random bot doesn't use this info)."""
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        """Randomly choose a target."""
        return random.choice(alive_players) if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """Randomly choose a card to give away."""
        return random.choice(self.hand) if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """Randomly choose a card type to request."""
        types = [CardType.DEFUSE, CardType.SKIP, CardType.ATTACK, CardType.SEE_THE_FUTURE]
        return random.choice(types)
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """Randomly choose from discard pile."""
        return random.choice(discard_pile) if discard_pile else None
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        """Randomly decide to nope with 20% probability."""
        return random.random() < 0.2
