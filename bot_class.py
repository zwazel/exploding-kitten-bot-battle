from abc import ABC, abstractmethod

from enum import Enum

class MoveType(Enum):
    PLAY_CARD = "play_card"
    DRAW_CARD = "draw_card"

class Bot(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def play(self, game_state: dict) -> dict:
        """
        Decide what to do during the bot's turn.
        Must return a dictionary like:
        {
            'move': MoveType.PLAY_CARD or MoveType.DRAW_CARD,
            'card': "Skip" or None if drawing
        }
        """
        pass
