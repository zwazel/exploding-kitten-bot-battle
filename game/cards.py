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
    CAT = "Cat"


@dataclass
class Card:
    """Represents a card in the game."""
    card_type: CardType

    def __str__(self):
        return self.card_type.value

    def __repr__(self):
        return f"Card({self.card_type.value})"
