"""
Event history system for recording all game actions.

Every action in the game creates a GameEvent that is recorded in the
GameHistory. This enables future replay functionality.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of events that can occur in the game."""
    
    # Game lifecycle
    GAME_START = "game_start"
    GAME_END = "game_end"
    
    # Turn events
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    
    # Card events
    CARD_DRAWN = "card_drawn"
    CARD_PLAYED = "card_played"
    CARD_DISCARDED = "card_discarded"
    COMBO_PLAYED = "combo_played"
    
    # Reaction events
    REACTION_ROUND_START = "reaction_round_start"
    REACTION_ROUND_END = "reaction_round_end"
    REACTION_PLAYED = "reaction_played"
    REACTION_SKIPPED = "reaction_skipped"
    
    # Player events
    PLAYER_JOINED = "player_joined"
    PLAYER_ELIMINATED = "player_eliminated"
    
    # Deck events
    DECK_SHUFFLED = "deck_shuffled"
    
    # Turn modification
    TURNS_ADDED = "turns_added"
    TURN_SKIPPED = "turn_skipped"


@dataclass(frozen=True)
class GameEvent:
    """
    An immutable record of something that happened in the game.
    
    Attributes:
        event_type: The type of event that occurred.
        step: The game step number when this event occurred.
        player_id: The player associated with this event, if any.
        data: Additional event-specific data.
    """
    
    event_type: EventType
    step: int
    player_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "step": self.step,
            "player_id": self.player_id,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameEvent:
        """Create a GameEvent from a dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            step=data["step"],
            player_id=data.get("player_id"),
            data=data.get("data", {}),
        )


class GameHistory:
    """
    Records all events that occur during a game.
    
    This class maintains an ordered list of GameEvents that can be
    used for replay functionality.
    """
    
    def __init__(self) -> None:
        """Initialize an empty game history."""
        self._events: list[GameEvent] = []
        self._current_step: int = 0
    
    @property
    def current_step(self) -> int:
        """Get the current game step number."""
        return self._current_step
    
    def record(
        self,
        event_type: EventType,
        player_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> GameEvent:
        """
        Record a new event in the history.
        
        Args:
            event_type: The type of event.
            player_id: The player associated with this event.
            data: Additional event data.
            
        Returns:
            The created GameEvent.
        """
        event: GameEvent = GameEvent(
            event_type=event_type,
            step=self._current_step,
            player_id=player_id,
            data=data or {},
        )
        self._events.append(event)
        self._current_step += 1
        return event
    
    def get_events(self) -> tuple[GameEvent, ...]:
        """
        Get all recorded events.
        
        Returns:
            An immutable tuple of all events in order.
        """
        return tuple(self._events)
    
    def get_events_since(self, step: int) -> tuple[GameEvent, ...]:
        """
        Get all events since a specific step.
        
        Args:
            step: The step number to start from (exclusive).
            
        Returns:
            Events that occurred after the given step.
        """
        return tuple(e for e in self._events if e.step > step)
    
    def get_events_by_type(self, event_type: EventType) -> tuple[GameEvent, ...]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: The type of events to retrieve.
            
        Returns:
            All events matching the given type.
        """
        return tuple(e for e in self._events if e.event_type == event_type)
    
    def to_json(self) -> str:
        """
        Serialize the entire history to JSON.
        
        Returns:
            A JSON string containing all events.
        """
        return json.dumps(
            {"events": [e.to_dict() for e in self._events]},
            indent=2,
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> GameHistory:
        """
        Deserialize a GameHistory from JSON.
        
        Args:
            json_str: The JSON string to parse.
            
        Returns:
            A GameHistory instance with the loaded events.
        """
        data: dict[str, Any] = json.loads(json_str)
        history: GameHistory = cls()
        for event_data in data["events"]:
            event: GameEvent = GameEvent.from_dict(event_data)
            history._events.append(event)
        if history._events:
            history._current_step = history._events[-1].step + 1
        return history
    
    def __len__(self) -> int:
        """Return the number of recorded events."""
        return len(self._events)
