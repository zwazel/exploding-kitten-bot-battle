from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    EXPLODING_KITTEN = "Exploding Kitten"
    DEFUSE = "Defuse"
    SKIP = "Skip"
    # ATTACK = "Attack"
    SEE_THE_FUTURE = "See the Future"
    NORMAL = "Normal"


@dataclass
class CardCounts:
    EXPLODING_KITTEN: int
    DEFUSE: int
    SKIP: int
    # ATTACK: int
    SEE_THE_FUTURE: int
    NORMAL: int


@dataclass
class Card:
    card_type: CardType
