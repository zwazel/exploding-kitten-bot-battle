from dataclasses import dataclass
from typing import List, Dict
from bot import Bot
from card import CardCounts

@dataclass
class GameState:
    bots: List[Bot]
    current_bot_index: int
    card_counts: CardCounts
    cards_left: int