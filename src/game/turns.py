"""
Turn and action management system.

This module handles turn order, extra turns, and the reaction round
system where players can respond to other players' actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.bots.base import Action, Bot
    from game.history import GameEvent


class RoundPhase(Enum):
    """Phases within a turn."""
    
    ACTION = auto()  # Player is taking their action
    REACTION = auto()  # Waiting for reactions from other players
    RESOLUTION = auto()  # Resolving the action (no more reactions)


@dataclass
class ReactionRound:
    """
    State for a reaction round.
    
    After a card is played, each player gets a chance to react.
    The order starts from the player after the one who triggered
    the reaction, going around the table.
    
    Attributes:
        triggering_event: The event that started this reaction round.
        triggering_player_id: Player who played the triggering card.
        pending_players: Players who haven't yet decided on reaction.
        reactions: List of (player_id, action) for players who reacted.
        is_cancelled: Whether the triggering action was cancelled.
    """
    
    triggering_event: GameEvent
    triggering_player_id: str
    pending_players: list[str] = field(default_factory=list)
    reactions: list[tuple[str, Action]] = field(default_factory=list)
    is_cancelled: bool = False


class TurnManager:
    """
    Manages turn order, extra turns, and reaction rounds.
    
    The turn manager tracks:
    - Which player's turn it is
    - How many turns a player has remaining (for attack cards)
    - Reaction rounds when cards are played
    """
    
    def __init__(self) -> None:
        """Initialize the turn manager."""
        self._turn_order: list[str] = []
        self._current_index: int = 0
        self._turns_remaining: dict[str, int] = {}
        self._phase: RoundPhase = RoundPhase.ACTION
        self._current_reaction_round: ReactionRound | None = None
    
    @property
    def phase(self) -> RoundPhase:
        """Get the current phase."""
        return self._phase
    
    @property
    def current_player_id(self) -> str | None:
        """Get the current player's ID."""
        if not self._turn_order:
            return None
        return self._turn_order[self._current_index]
    
    @property
    def turn_order(self) -> tuple[str, ...]:
        """Get the turn order as an immutable tuple."""
        return tuple(self._turn_order)
    
    def setup(self, player_ids: list[str]) -> None:
        """
        Set up the turn order.
        
        Args:
            player_ids: List of player IDs in turn order.
        """
        self._turn_order = player_ids.copy()
        self._current_index = 0
        self._turns_remaining = {pid: 1 for pid in player_ids}
    
    def get_turns_remaining(self, player_id: str) -> int:
        """Get how many turns a player has remaining."""
        return self._turns_remaining.get(player_id, 0)
    
    def set_turns_remaining(self, player_id: str, turns: int) -> None:
        """Set how many turns a player has remaining."""
        self._turns_remaining[player_id] = max(0, turns)
    
    def add_turns(self, player_id: str, extra_turns: int) -> None:
        """Add extra turns for a player."""
        current: int = self._turns_remaining.get(player_id, 0)
        self._turns_remaining[player_id] = current + extra_turns
    
    def consume_turn(self, player_id: str) -> bool:
        """
        Consume one turn for the player.
        
        Returns:
            True if the player still has turns remaining, False if done.
        """
        current: int = self._turns_remaining.get(player_id, 0)
        if current > 0:
            self._turns_remaining[player_id] = current - 1
        return self._turns_remaining.get(player_id, 0) > 0
    
    def skip_turn(self, player_id: str) -> None:
        """Skip the current turn (e.g., from a skip card)."""
        # Just consume the turn without the player having to draw
        self.consume_turn(player_id)
    
    def advance_to_next_player(self, alive_players: list[str]) -> str | None:
        """
        Advance to the next alive player in turn order.
        
        Args:
            alive_players: List of player IDs still in the game.
            
        Returns:
            The new current player's ID, or None if no players.
        """
        if not alive_players or not self._turn_order:
            return None
        
        # Find next alive player
        start_index: int = self._current_index
        for _ in range(len(self._turn_order)):
            self._current_index = (self._current_index + 1) % len(self._turn_order)
            current_id: str = self._turn_order[self._current_index]
            if current_id in alive_players:
                # Reset turns for new player
                self._turns_remaining[current_id] = 1
                return current_id
            if self._current_index == start_index:
                break
        
        return self.current_player_id
    
    def start_reaction_round(
        self,
        triggering_event: GameEvent,
        triggering_player_id: str,
        alive_players: list[str],
    ) -> ReactionRound:
        """
        Start a reaction round after a card is played.
        
        Players are ordered starting from the player after the one
        who played the triggering card.
        
        Args:
            triggering_event: The event that triggered this round.
            triggering_player_id: Player who triggered the round.
            alive_players: All players still in the game.
            
        Returns:
            The new ReactionRound.
        """
        self._phase = RoundPhase.REACTION
        
        # Build reaction order starting from player after triggering player
        reaction_order: list[str] = []
        if triggering_player_id in self._turn_order:
            trigger_idx: int = self._turn_order.index(triggering_player_id)
            for i in range(1, len(self._turn_order)):
                idx: int = (trigger_idx + i) % len(self._turn_order)
                player_id: str = self._turn_order[idx]
                if player_id in alive_players and player_id != triggering_player_id:
                    reaction_order.append(player_id)
        
        self._current_reaction_round = ReactionRound(
            triggering_event=triggering_event,
            triggering_player_id=triggering_player_id,
            pending_players=reaction_order,
        )
        
        return self._current_reaction_round
    
    def get_current_reaction_round(self) -> ReactionRound | None:
        """Get the current reaction round, if any."""
        return self._current_reaction_round
    
    def end_reaction_round(self) -> ReactionRound | None:
        """
        End the current reaction round and return to action phase.
        
        Returns:
            The completed reaction round.
        """
        completed: ReactionRound | None = self._current_reaction_round
        self._current_reaction_round = None
        self._phase = RoundPhase.RESOLUTION
        return completed
    
    def remove_player(self, player_id: str) -> None:
        """Remove a player from the turn order (when eliminated)."""
        if player_id in self._turn_order:
            removed_idx: int = self._turn_order.index(player_id)
            self._turn_order.remove(player_id)
            
            # Adjust current index if needed
            if self._turn_order:
                if removed_idx < self._current_index:
                    self._current_index -= 1
                elif removed_idx == self._current_index:
                    self._current_index = self._current_index % len(self._turn_order)
            
        if player_id in self._turns_remaining:
            del self._turns_remaining[player_id]
