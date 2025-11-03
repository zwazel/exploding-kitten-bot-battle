"""Base Bot class that all bots must inherit from."""

from abc import ABC, abstractmethod
from typing import Optional, List
from .cards import Card
from .game_state import GameState


class Bot(ABC):
    """
    Base class for all bots in the Exploding Kittens game.
    
    All bots must inherit from this class and implement the required methods.
    """

    def __init__(self, name: str):
        """
        Initialize the bot.
        
        Args:
            name: The name of the bot (typically the filename without .py extension)
        """
        self.name = name
        self.hand: List[Card] = []
        self.alive = True

    @abstractmethod
    def play(self, state: GameState) -> Optional[Card]:
        """
        Called when it's the bot's turn to play a card.
        
        Args:
            state: The current game state
            
        Returns:
            The card to play, or None to end the turn without playing a card
        """
        pass

    @abstractmethod
    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Called when the bot draws an Exploding Kitten and has a Defuse card.
        
        Args:
            state: The current game state
            
        Returns:
            The index (0-based) in the draw pile where to insert the Exploding Kitten.
            0 means top of the deck, state.cards_left_to_draw means bottom.
        """
        pass

    @abstractmethod
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Called when the bot plays a "See the Future" card.
        
        Args:
            state: The current game state
            top_three: The top three cards of the draw pile (index 0 is the top card)
        """
        pass

    def has_card(self, card: Card) -> bool:
        """Check if the bot has a specific card in hand."""
        return card in self.hand

    def has_card_type(self, card_type) -> bool:
        """Check if the bot has any card of a specific type."""
        return any(card.card_type == card_type for card in self.hand)

    def remove_card(self, card: Card) -> bool:
        """
        Remove a card from the bot's hand.
        
        Args:
            card: The card to remove
            
        Returns:
            True if the card was removed, False if it wasn't in the hand
        """
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def add_card(self, card: Card) -> None:
        """Add a card to the bot's hand."""
        self.hand.append(card)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Bot({self.name})"
