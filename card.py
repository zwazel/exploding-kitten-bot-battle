from dataclasses import dataclass, field
from enum import Enum
import uuid


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
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
