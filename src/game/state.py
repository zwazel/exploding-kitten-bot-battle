"""
Protected game state container.

This module contains the internal game state that should NEVER be
exposed directly to bots. Bots receive a BotView instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.cards.base import Card


@dataclass
class PlayerState:
    """
    Internal state for a single player.
    
    Attributes:
        player_id: Unique identifier for the player.
        hand: The cards in the player's hand.
        is_alive: Whether the player is still in the game.
        turns_remaining: Number of turns the player must take before ending.
    """
    
    player_id: str
    hand: list[Card] = field(default_factory=list)
    is_alive: bool = True
    turns_remaining: int = 1


class GameState:
    """
    The complete internal state of the game.
    
    This class is NEVER exposed to bots. The GameEngine uses this
    to track the true state, and creates BotView instances for bots.
    
    Attributes:
        draw_pile: Cards that can be drawn.
        discard_pile: Cards that have been discarded.
        players: All players in the game.
        turn_order: Order in which players take turns.
        current_player_index: Index into turn_order for current player.
    """
    
    def __init__(self) -> None:
        """Initialize an empty game state."""
        self._draw_pile: list[Card] = []
        self._discard_pile: list[Card] = []
        self._players: dict[str, PlayerState] = {}
        self._turn_order: list[str] = []
        self._current_player_index: int = 0
    
    # --- Draw Pile ---
    
    @property
    def draw_pile(self) -> list[Card]:
        """Get the draw pile (mutable - engine only)."""
        return self._draw_pile
    
    @property
    def draw_pile_count(self) -> int:
        """Get the number of cards in the draw pile."""
        return len(self._draw_pile)
    
    def draw_card(self) -> Card | None:
        """
        Draw the top card from the draw pile.
        
        Returns:
            The drawn card, or None if the pile is empty.
        """
        if self._draw_pile:
            return self._draw_pile.pop(0)  # Index 0 is the top
        return None
    
    def add_to_draw_pile(self, card: Card) -> None:
        """Add a card to the top of the draw pile."""
        self._draw_pile.insert(0, card)  # Index 0 is the top
    
    def insert_in_draw_pile(self, card: Card, position: int) -> None:
        """
        Insert a card at a specific position in the draw pile.
        
        Args:
            card: The card to insert.
            position: 0 = top (next to draw), len(draw_pile) = bottom.
        """
        position = max(0, min(position, len(self._draw_pile)))
        self._draw_pile.insert(position, card)
    
    # --- Discard Pile ---
    
    @property
    def discard_pile(self) -> list[Card]:
        """Get the discard pile (mutable - engine only)."""
        return self._discard_pile
    
    def discard(self, card: Card) -> None:
        """Add a card to the discard pile."""
        self._discard_pile.append(card)
    
    # --- Players ---
    
    @property
    def players(self) -> dict[str, PlayerState]:
        """Get all player states."""
        return self._players
    
    def add_player(self, player_id: str) -> PlayerState:
        """
        Add a new player to the game.
        
        Args:
            player_id: Unique identifier for the player.
            
        Returns:
            The created PlayerState.
        """
        player: PlayerState = PlayerState(player_id=player_id)
        self._players[player_id] = player
        return player
    
    def get_player(self, player_id: str) -> PlayerState | None:
        """Get a player by ID."""
        return self._players.get(player_id)
    
    def get_player_hand(self, player_id: str) -> list[Card]:
        """Get a player's hand."""
        player: PlayerState | None = self._players.get(player_id)
        if player:
            return player.hand
        return []
    
    def get_alive_players(self) -> list[str]:
        """Get IDs of all players still in the game."""
        return [pid for pid, p in self._players.items() if p.is_alive]
    
    # --- Turn Order ---
    
    @property
    def turn_order(self) -> list[str]:
        """Get the turn order (mutable - engine only)."""
        return self._turn_order
    
    @property
    def current_player_index(self) -> int:
        """Get the current player index."""
        return self._current_player_index
    
    @current_player_index.setter
    def current_player_index(self, value: int) -> None:
        """Set the current player index."""
        self._current_player_index = value
    
    @property
    def current_player_id(self) -> str | None:
        """Get the current player's ID."""
        if not self._turn_order:
            return None
        return self._turn_order[self._current_player_index]
    
    def get_current_player(self) -> PlayerState | None:
        """Get the current player's state."""
        current_id: str | None = self.current_player_id
        if current_id:
            return self._players.get(current_id)
        return None
    
    def advance_turn(self) -> str | None:
        """
        Advance to the next alive player.
        
        Returns:
            The new current player's ID, or None if no players alive.
        """
        if not self._turn_order:
            return None
        
        alive_players: list[str] = self.get_alive_players()
        if not alive_players:
            return None
        
        # Find next alive player
        start_index: int = self._current_player_index
        for _ in range(len(self._turn_order)):
            self._current_player_index = (
                (self._current_player_index + 1) % len(self._turn_order)
            )
            current_id: str = self._turn_order[self._current_player_index]
            if current_id in alive_players:
                return current_id
            # Safety: don't loop forever if we've checked everyone
            if self._current_player_index == start_index:
                break
        
        return self.current_player_id
