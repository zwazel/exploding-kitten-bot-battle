from enum import Enum, auto
from dataclasses import dataclass

class CardType(Enum):
    EXPLODING_KITTEN = auto()
    DEFUSE = auto()
    SKIP = auto()
    ATTACK = auto()
    SEE_THE_FUTURE = auto()
    NORMAL = auto()

@dataclass
class Card:
    card_type: CardType

@dataclass
class CardCounts:
    EXPLODING_KITTEN: int
    DEFUSE: int
    SKIP: int
    ATTACK: int
    SEE_THE_FUTURE: int
    NORMAL: int