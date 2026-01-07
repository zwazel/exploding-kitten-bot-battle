"""
Abstract base class for all cards in the game.

Each card type extends this class and implements its own behavior
for when it can be played and what happens when it is played.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.bots.view import BotView
    from game.engine import GameEngine


class Card(ABC):
    """
    Abstract base class for all cards.
    
    Card implementations define their own behavior through the abstract
    methods below. This allows each card type to control when it can be
    played, whether it can be played as a reaction, and what effect it has.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        The display name of this card.
        
        Returns:
            A human-readable name for the card.
        """
        ...
    
    @property
    @abstractmethod
    def card_type(self) -> str:
        """
        The type identifier for this card.
        
        Used for deck configuration and card matching.
        
        Returns:
            A string identifier (e.g., "skip", "nope", "defuse").
        """
        ...
    
    @abstractmethod
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        """
        Check if this card can be played in the current game state.
        
        Args:
            view: The bot's view of the game state.
            is_own_turn: Whether it's currently the bot's turn.
            
        Returns:
            True if the card can be played, False otherwise.
        """
        ...
    
    @abstractmethod
    def can_play_as_reaction(self) -> bool:
        """
        Check if this card can be played as a reaction (out of turn).
        
        Reaction cards can be played during the reaction round after
        another player plays a card.
        
        Returns:
            True if this card can be played as a reaction.
        """
        ...
    
    @abstractmethod
    def execute(self, engine: GameEngine, player_id: str) -> None:
        """
        Execute the card's effect.
        
        This is called by the GameEngine when the card is played.
        The card can modify game state through the engine's methods.
        
        Args:
            engine: The game engine (for modifying state).
            player_id: The ID of the player who played the card.
        """
        ...
    
    def can_combo(self) -> bool:
        """
        Check if this card can be part of a combo.
        
        Combo rules (handled by engine):
        - 2 of a kind: steal a random card from a chosen player
        - 3 of a kind: name a card and steal it if target has it
        - 5 different cards: draw from discard pile
        
        Override this in card implementations that support combos.
        
        Returns:
            True if this card can be used in a combo.
        """
        return False
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(name={self.name!r})"
    
    def __eq__(self, other: object) -> bool:
        """Cards are equal if they are the same instance."""
        return self is other
    
    def __hash__(self) -> int:
        """Hash based on object identity."""
        return id(self)
