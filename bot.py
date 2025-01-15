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
        """
        - This method is called when it's your turn to play
        - You need to return the card you want to play, or None if you want to end your turn without playing anything
        """
        pass

    @abstractmethod
    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        - This method is called when you draw an exploding kitten card and had a defuse card in your hand
        - As you're still alive, you need to put the exploding kitten card back into your hand
        - You can choose where to put it back, so you need to return the index of the draw pile in which you want to put the card in
        """
        pass

    @abstractmethod
    def see_the_future(self, state: GameState, top_three: List[Card]):
        """
        - This method is called when you play a "See the future" card
        - You can see the top three cards of the draw pile
        """
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