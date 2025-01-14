from abc import ABC, abstractmethod
from typing import List, Optional
from card import Card, CardType

class Bot(ABC):
    def __init__(self, name: str):
        self.name = name
        self.hand: List[Card] = []
        self.last_five_played: List[Card] = []

    @abstractmethod
    def play(self, cards_left: int) -> Optional[Card]:
        pass

    @abstractmethod
    def handle_exploding_kitten(self) -> int:
        pass

    @abstractmethod
    def see_the_future(self, top_three: List[Card]):
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

    def add_last_played(self, card: Card):
        self.last_five_played.append(card)
        if len(self.last_five_played) > 5:
            self.last_five_played.pop(0)