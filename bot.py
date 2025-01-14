from abc import ABC, abstractmethod
from typing import List, Optional
from card import Card, CardType
from game_handling.game_state import GameState


class Bot(ABC):
    def __init__(self, name: str):
        self.alive: bool = True
        self.name: str = name
        self.hand: List[Card] = []

    @abstractmethod
    def play(self, state: GameState) -> Optional[Card]:
        pass

    @abstractmethod
    def handle_exploding_kitten(self, state: GameState) -> int:
        pass

    @abstractmethod
    def see_the_future(self, state: GameState, top_three: List[Card]):
        pass

    def add_card(self, card: Card):
        self.hand.append(card)

    def remove_card(self, card: Card):
        self.hand.remove(card)

    def has_defuse(self) -> bool:
        return any(card.card_type == CardType.DEFUSE for card in self.hand)

    def use_defuse(self) -> Card:
        defuse = next(card for card in self.hand if card.card_type == CardType.DEFUSE)
        self.remove_card(defuse)
        return defuse