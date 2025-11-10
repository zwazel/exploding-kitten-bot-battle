"""GameState class that provides game information to bots."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from .cards import Card, CardType


@dataclass
class GameState:
    """
    Represents the current state of the game visible to bots.
    
    This contains all public information that bots can use to make decisions.
    
    Note: While this class is not frozen, bots should treat it as read-only.
    The game engine creates copies before passing to bots to prevent direct modification.
    
    Attributes:
        initial_card_counts: How many of each card type existed at game start (read-only)
        cards_left_to_draw: Current number of cards remaining in draw pile
        was_last_card_exploding_kitten: Whether the last drawn card was an Exploding Kitten
        history_of_played_cards: Tuple of all cards played so far (in order) - immutable
        alive_bots: Number of bots still alive in the game
    """
    initial_card_counts: Dict[CardType, int]
    cards_left_to_draw: int
    was_last_card_exploding_kitten: bool
    history_of_played_cards: Tuple[Card, ...] = field(default_factory=tuple)
    alive_bots: int = 0

    def copy(self) -> 'GameState':
        """
        Create a deep copy of the game state.
        
        This ensures that modifications to the copy cannot affect the original game state.
        All nested structures are deeply copied.
        """
        return GameState(
            initial_card_counts=self.initial_card_counts.copy(),
            cards_left_to_draw=self.cards_left_to_draw,
            was_last_card_exploding_kitten=self.was_last_card_exploding_kitten,
            history_of_played_cards=tuple(self.history_of_played_cards),
            alive_bots=self.alive_bots,
        )
