"""
This defines the interface every bot must follow:
- play(): The required method every bot must implement.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import TypedDict, Optional

class MoveType(Enum):
    PLAY_CARD = "play_card"
    DRAW_CARD = "draw_card"

class Move(TypedDict):
    move: MoveType
    card: Optional[str]

class Bot(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def play(self, game_state: dict) -> Move:
        """
        Return a move dict:
        {
            'move': MoveType.PLAY_CARD or MoveType.DRAW_CARD,
            'card': <card_type> or None if drawing a card
        }
        """
        pass