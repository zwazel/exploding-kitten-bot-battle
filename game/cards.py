"""Card definitions for Exploding Kittens game."""

from enum import Enum
from dataclasses import dataclass


class CardType(Enum):
    """Types of cards in Exploding Kittens."""
    EXPLODING_KITTEN = "Exploding Kitten"
    DEFUSE = "Defuse"
    SKIP = "Skip"
    SEE_THE_FUTURE = "See the Future"
    SHUFFLE = "Shuffle"
    FAVOR = "Favor"
    ATTACK = "Attack"
    NOPE = "Nope"
    # Cat cards for combos
    TACOCAT = "Tacocat"
    CATTERMELON = "Cattermelon"
    HAIRY_POTATO_CAT = "Hairy Potato Cat"
    BEARD_CAT = "Beard Cat"
    RAINBOW_RALPHING_CAT = "Rainbow-Ralphing Cat"


class ComboType(Enum):
    """Types of card combos in Exploding Kittens."""
    TWO_OF_A_KIND = "2-of-a-kind"
    THREE_OF_A_KIND = "3-of-a-kind"
    FIVE_UNIQUE = "5-unique"


class TargetContext(Enum):
    """Contexts for choosing a target player."""
    FAVOR = "favor"
    TWO_OF_A_KIND = "2-of-a-kind"
    THREE_OF_A_KIND = "3-of-a-kind"


@dataclass
class Card:
    """Represents a card in the game."""
    card_type: CardType

    def __str__(self):
        return self.card_type.value

    def __repr__(self):
        return f"Card({self.card_type.value})"
