""" This file contains the abstract Bot class """
from abc import ABC, abstractmethod
from typing import List, Optional

from card import Card, CardType
from game_handling.game_state import GameState


class Bot(ABC):
    """
    Abstract class that needs to be inherited by any bot that wants to play the game
    """

    def __init__(self, name: str):
        """
        Constructor for the Bot class
        :param name: str name of the bot
        """
        self._alive: bool = True
        self._name: str = name
        self._hand: List[Card] = []

    def __repr__(self):
        return self.name

    @abstractmethod
    def play(self, state: GameState) -> Optional[Card]:
        """
        This method is called when it's your turn to play
        You need to return the card you want to play, or None if you want to end your turn without playing anything
        :param state: GameState object
        :return: Card object or None
        """
        pass

    @abstractmethod
    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        This method is called when you draw an exploding kitten card and had a defuse card in your hand
        As you're still alive, you need to put the exploding kitten card back into your hand
        You can choose where to put it back, so you need to return the index of the draw pile
        where you want to place the card
        :param state: GameState object
        :return: int index of the draw pile
        """
        pass


    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        - This method is called when you play a "See the future" card
        - You can see the top three cards of the draw pile
        :param state: GameState object
        :param top_three: List of top three cards of the draw pile
        :return: None
        """
        pass


    def card_played(self, card_type: CardType, position: int) -> bool:
        """
        This method is called when a card is played by another bot
        :param card_type: Type of the card that was played
        :param position: Position of the bot that played the card
        - 0=you
        - 1=previous bot, you will be next
        - 2=two spots away, you will be after the next turn
        - etc.
        :return: True=Play a "Nope" card, False=Don't play a "Nope" card
        """
        return False

    def card_drawn(self, position: int) -> None:
        """
        This method is called when a card is drawn by a bot
        :param position: Position of the bot that drew the card
        """
        pass

    def add_card(self, card: Card):
        """
        Adds a card to the bot's hand
        :param card: Card object
        :return: None
        """
        self.hand.append(card)

    def remove_card(self, card: Card):
        """
        Removes a card from the bot's hand
        :param card: Card object
        :return: None
        """
        self.hand.remove(card)

    def has_defuse(self) -> bool:
        """
        Returns True if the bot has a defuse card in its hand
        :return: bool
        """
        return any(card.card_type == CardType.DEFUSE for card in self.hand)

    def use_defuse(self) -> Card:
        """
        Removes and returns a defuse card from the bot's hand
        :return: Card object
        """
        defuse = next(card for card in self.hand if card.card_type == CardType.DEFUSE)
        self.remove_card(defuse)
        return defuse

    @property
    def alive(self):
        """ returns the alive """
        return self._alive

    @alive.setter
    def alive(self, value):
        """ sets the alive """
        self._alive = value

    @property
    def name(self):
        """ returns the name """
        return self._name

    @name.setter
    def name(self, value):
        """ sets the name """
        self._name = value

    @property
    def hand(self):
        """ returns the hand """
        return self._hand

    @hand.setter
    def hand(self, value):
        """ sets the hand """
        self._hand = value
