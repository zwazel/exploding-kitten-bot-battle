""" Provides the Card class and CardType enum for the game. """
from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    """
    Enum for the different types of cards in the game
    """
    EXPLODING_KITTEN = 'Exploding Kitten'
    DEFUSE = 'Defuse'
    SKIP = 'Skip'
    ATTACK = 'Attack'
    SEE_THE_FUTURE = 'See the Future'
    NORMAL = 'Normal'
    SHUFFLE = 'Shuffle'


@dataclass
class CardCounts:
    """
    Dataclass for the amount of each card type in the game
    """
    EXPLODING_KITTEN: int
    DEFUSE: int
    SKIP: int
    ATTACK: int
    SEE_THE_FUTURE: int
    NORMAL: int
    SHUFFLE: int


@dataclass
class Card:
    """
    Dataclass for a card in the game
    """
    card_type: CardType
