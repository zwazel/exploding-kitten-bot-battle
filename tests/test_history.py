"""
Tests for the event history system.

These tests verify that all game events are properly recorded
and can be serialized/deserialized for replay.
"""

import json
import pytest

from game.history import EventType, GameEvent, GameHistory


class TestGameEvent:
    """Tests for the GameEvent dataclass."""
    
    def test_event_creation(self) -> None:
        """Events should be created with correct attributes."""
        event: GameEvent = GameEvent(
            event_type=EventType.CARD_PLAYED,
            step=5,
            player_id="player1",
            data={"card_type": "SkipCard"},
        )
        
        assert event.event_type == EventType.CARD_PLAYED
        assert event.step == 5
        assert event.player_id == "player1"
        assert event.data["card_type"] == "SkipCard"
    
    def test_event_is_immutable(self) -> None:
        """Events should be immutable (frozen dataclass)."""
        event: GameEvent = GameEvent(
            event_type=EventType.CARD_PLAYED,
            step=5,
            player_id="player1",
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            event.step = 10  # type: ignore[misc]
    
    def test_event_to_dict(self) -> None:
        """Events should serialize to dictionary."""
        event: GameEvent = GameEvent(
            event_type=EventType.CARD_DRAWN,
            step=3,
            player_id="player2",
            data={"card_type": "NopeCard"},
        )
        
        result: dict = event.to_dict()
        
        assert result["event_type"] == "card_drawn"
        assert result["step"] == 3
        assert result["player_id"] == "player2"
        assert result["data"]["card_type"] == "NopeCard"
    
    def test_event_from_dict(self) -> None:
        """Events should deserialize from dictionary."""
        data: dict = {
            "event_type": "turn_start",
            "step": 10,
            "player_id": "player1",
            "data": {},
        }
        
        event: GameEvent = GameEvent.from_dict(data)
        
        assert event.event_type == EventType.TURN_START
        assert event.step == 10
        assert event.player_id == "player1"


class TestGameHistory:
    """Tests for the GameHistory class."""
    
    def test_record_event(self) -> None:
        """Recording events should add them to history."""
        history: GameHistory = GameHistory()
        
        event: GameEvent = history.record(
            EventType.GAME_START,
            data={"turn_order": ["p1", "p2"]},
        )
        
        assert len(history) == 1
        assert event.event_type == EventType.GAME_START
        assert event.step == 0
    
    def test_step_increments(self) -> None:
        """Each recorded event should have an incrementing step."""
        history: GameHistory = GameHistory()
        
        event1: GameEvent = history.record(EventType.GAME_START)
        event2: GameEvent = history.record(EventType.TURN_START, "player1")
        event3: GameEvent = history.record(EventType.CARD_DRAWN, "player1")
        
        assert event1.step == 0
        assert event2.step == 1
        assert event3.step == 2
    
    def test_get_events_returns_immutable(self) -> None:
        """get_events should return an immutable tuple."""
        history: GameHistory = GameHistory()
        history.record(EventType.GAME_START)
        
        events: tuple[GameEvent, ...] = history.get_events()
        
        assert isinstance(events, tuple)
    
    def test_get_events_since(self) -> None:
        """get_events_since should filter by step."""
        history: GameHistory = GameHistory()
        history.record(EventType.GAME_START)  # step 0
        history.record(EventType.TURN_START)  # step 1
        history.record(EventType.CARD_DRAWN)  # step 2
        history.record(EventType.TURN_END)    # step 3
        
        events: tuple[GameEvent, ...] = history.get_events_since(1)
        
        assert len(events) == 2  # steps 2 and 3
        assert events[0].step == 2
        assert events[1].step == 3
    
    def test_get_events_by_type(self) -> None:
        """get_events_by_type should filter by event type."""
        history: GameHistory = GameHistory()
        history.record(EventType.TURN_START, "p1")
        history.record(EventType.CARD_DRAWN, "p1")
        history.record(EventType.TURN_END, "p1")
        history.record(EventType.TURN_START, "p2")
        history.record(EventType.CARD_DRAWN, "p2")
        
        turn_starts: tuple[GameEvent, ...] = history.get_events_by_type(
            EventType.TURN_START
        )
        
        assert len(turn_starts) == 2
    
    def test_json_serialization(self) -> None:
        """History should serialize to and from JSON."""
        history: GameHistory = GameHistory()
        history.record(EventType.GAME_START, data={"seed": 42})
        history.record(EventType.TURN_START, "player1")
        history.record(EventType.CARD_PLAYED, "player1", {"card_type": "Skip"})
        
        json_str: str = history.to_json()
        
        # Verify it's valid JSON
        parsed: dict = json.loads(json_str)
        assert "events" in parsed
        assert len(parsed["events"]) == 3
        
        # Verify deserialization
        restored: GameHistory = GameHistory.from_json(json_str)
        assert len(restored) == 3
        
        original_events: tuple = history.get_events()
        restored_events: tuple = restored.get_events()
        
        for orig, rest in zip(original_events, restored_events):
            assert orig.event_type == rest.event_type
            assert orig.step == rest.step
            assert orig.player_id == rest.player_id
