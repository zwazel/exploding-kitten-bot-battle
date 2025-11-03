"""GameState class that provides game information to bots."""

from dataclasses import dataclass, field
from typing import List, Dict
from .cards import Card, CardType


@dataclass
class CardCounts:
    """Count of each card type in the deck."""
    exploding_kitten: int = 0
    defuse: int = 0
    skip: int = 0
    see_the_future: int = 0
    shuffle: int = 0
    favor: int = 0
    attack: int = 0
    nope: int = 0
    tacocat: int = 0
    cattermelon: int = 0
    hairy_potato_cat: int = 0
    beard_cat: int = 0
    rainbow_ralphing_cat: int = 0

    def to_dict(self) -> Dict[CardType, int]:
        """Convert to dictionary mapping CardType to count."""
        return {
            CardType.EXPLODING_KITTEN: self.exploding_kitten,
            CardType.DEFUSE: self.defuse,
            CardType.SKIP: self.skip,
            CardType.SEE_THE_FUTURE: self.see_the_future,
            CardType.SHUFFLE: self.shuffle,
            CardType.FAVOR: self.favor,
            CardType.ATTACK: self.attack,
            CardType.NOPE: self.nope,
            CardType.TACOCAT: self.tacocat,
            CardType.CATTERMELON: self.cattermelon,
            CardType.HAIRY_POTATO_CAT: self.hairy_potato_cat,
            CardType.BEARD_CAT: self.beard_cat,
            CardType.RAINBOW_RALPHING_CAT: self.rainbow_ralphing_cat,
        }


@dataclass
class GameState:
    """
    Represents the current state of the game visible to bots.
    
    This contains all public information that bots can use to make decisions.
    """
    total_cards_in_deck: CardCounts
    cards_left_to_draw: int
    was_last_card_exploding_kitten: bool
    history_of_played_cards: List[Card] = field(default_factory=list)
    alive_bots: int = 0

    def copy(self) -> 'GameState':
        """Create a copy of the game state."""
        return GameState(
            total_cards_in_deck=self.total_cards_in_deck,
            cards_left_to_draw=self.cards_left_to_draw,
            was_last_card_exploding_kitten=self.was_last_card_exploding_kitten,
            history_of_played_cards=self.history_of_played_cards.copy(),
            alive_bots=self.alive_bots,
        )
