"""
Abstract base class for all bots.

Bots implement this interface to participate in the game. The interface
provides methods for taking turns, reacting to events, and responding
during reaction rounds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.bots.view import BotView
    from game.cards.base import Card
    from game.history import GameEvent


@dataclass(frozen=True)
class PlayCardAction:
    """Action to play a single card."""
    
    card: Card
    target_player_id: str | None = None  # For cards that target a player


@dataclass(frozen=True)
class PlayComboAction:
    """Action to play a combo of cards."""
    
    cards: tuple[Card, ...]
    target_player_id: str | None = None


@dataclass(frozen=True)
class DrawCardAction:
    """Action to draw a card (end turn normally)."""
    
    pass


@dataclass(frozen=True)
class PassAction:
    """Action to pass (do nothing / decline to react)."""
    
    pass


# Type alias for all possible actions
Action = PlayCardAction | PlayComboAction | DrawCardAction | PassAction


class Bot(ABC):
    """
    Abstract base class for all bots.
    
    Bot implementations must provide:
    - A name for identification
    - Logic for taking turns
    - Logic for observing events
    - Logic for reacting during reaction rounds
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        The display name of this bot.
        
        Returns:
            A human-readable name for the bot.
        """
        ...
    
    @abstractmethod
    def take_turn(self, view: BotView) -> Action:
        """
        Called when it's this bot's turn to play.
        
        The bot should decide what action to take based on the current
        game state (visible through the view).
        
        Args:
            view: The bot's view of the game state.
            
        Returns:
            The action to take. Return DrawCardAction to end the turn
            by drawing a card.
        """
        ...
    
    @abstractmethod
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """
        Called when any game event occurs.
        
        This is for information only - the bot cannot take action here.
        Use this to track game state and other players' actions.
        
        Args:
            event: The event that occurred.
            view: The bot's current view of the game state.
        """
        ...
    
    @abstractmethod
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Called during a reaction round to allow playing reaction cards.
        
        This is called after another player plays a card, giving this bot
        a chance to play a reaction card (like Nope) if it has one.
        
        Args:
            view: The bot's view of the game state.
            triggering_event: The event that triggered this reaction round.
            
        Returns:
            An action to take (typically PlayCardAction with a reaction card),
            or None to decline reacting.
        """
        ...
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(name={self.name!r})"
