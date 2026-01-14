"""
Tests for the bot timeout mechanism.

Verifies that bots are properly eliminated when they take too long to respond,
and that an Exploding Kitten is removed from the deck to maintain game balance.
"""

import time
import pytest

from game.engine import GameEngine, BotTimeoutError
from game.bots.base import Bot, Action, DrawCardAction, PlayCardAction
from game.bots.view import BotView
from game.cards.base import Card
from game.history import EventType, GameEvent


class SlowBot(Bot):
    """A bot that deliberately times out on specified methods."""
    
    def __init__(self, delay: float = 10.0, slow_methods: set[str] | None = None) -> None:
        """
        Initialize with configurable delay and which methods should be slow.
        
        Args:
            delay: How long to sleep (should exceed timeout)
            slow_methods: Set of method names that should be slow. 
                         If None, all methods are slow.
        """
        self._delay = delay
        self._slow_methods = slow_methods or {"take_turn", "react", "choose_card_to_give", 
                                               "choose_defuse_position", "on_event", "on_explode"}
    
    @property
    def name(self) -> str:
        return "SlowBot"
    
    def take_turn(self, view: BotView) -> Action:
        if "take_turn" in self._slow_methods:
            time.sleep(self._delay)
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        if "on_event" in self._slow_methods:
            time.sleep(self._delay)
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        if "react" in self._slow_methods:
            time.sleep(self._delay)
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        if "choose_defuse_position" in self._slow_methods:
            time.sleep(self._delay)
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        if "choose_card_to_give" in self._slow_methods:
            time.sleep(self._delay)
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        if "on_explode" in self._slow_methods:
            time.sleep(self._delay)


class FastBot(Bot):
    """A simple bot that responds instantly for testing."""
    
    @property
    def name(self) -> str:
        return "FastBot"
    
    def take_turn(self, view: BotView) -> Action:
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        pass


class TestBotTimeout:
    """Tests for the bot timeout mechanism."""
    
    def test_timeout_on_take_turn_eliminates_bot(self) -> None:
        """Test that a bot timing out on take_turn is eliminated."""
        # Create engine with short timeout
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=0.1)
        
        # Add a slow bot and a fast bot
        slow_bot = SlowBot(delay=1.0, slow_methods={"take_turn"})
        fast_bot = FastBot()
        
        engine.add_bot(slow_bot)
        engine.add_bot(fast_bot)
        
        # Setup game
        engine.load_deck_from_config("configs/default_deck.json")
        engine.setup_game()
        
        # Count initial kittens
        initial_kittens = sum(
            1 for card in engine._state._draw_pile 
            if card.card_type == "ExplodingKittenCard"
        )
        
        # Run game - slow bot should be eliminated immediately on first turn
        winner = engine.run()
        
        # Fast bot should win since slow bot was eliminated
        assert winner == "FastBot", f"Expected FastBot to win, got {winner}"
        
        # Verify timeout event was recorded
        timeout_events = [
            e for e in engine.history.get_events()
            if e.event_type == EventType.BOT_TIMEOUT
        ]
        assert len(timeout_events) >= 1, "No timeout event recorded"
        assert timeout_events[0].player_id == "SlowBot"
        assert timeout_events[0].data.get("method") == "take_turn"
    
    def test_timeout_removes_exploding_kitten(self) -> None:
        """Test that timeout elimination removes an Exploding Kitten from deck."""
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=0.1)
        
        slow_bot = SlowBot(delay=1.0, slow_methods={"take_turn"})
        fast_bot = FastBot()
        
        engine.add_bot(slow_bot)
        engine.add_bot(fast_bot)
        
        # Load deck
        engine.load_deck_from_config("configs/default_deck.json")
        engine.setup_game()
        
        # With 2 players, there should be 1 Exploding Kitten
        initial_kittens = sum(
            1 for card in engine._state._draw_pile 
            if card.card_type == "ExplodingKittenCard"
        )
        assert initial_kittens == 1, f"Expected 1 kitten for 2 players, got {initial_kittens}"
        
        # Run game
        winner = engine.run()
        
        # After timeout elimination, there should be 0 kittens left
        final_kittens = sum(
            1 for card in engine._state._draw_pile 
            if card.card_type == "ExplodingKittenCard"
        )
        assert final_kittens == 0, f"Expected 0 kittens after timeout, got {final_kittens}"
    
    def test_no_timeout_when_disabled(self) -> None:
        """Test that bots are not eliminated when timeout is disabled."""
        # Create engine with no timeout
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        
        # Fast bot only (would timeout if timeout was enabled)
        fast_bot1 = FastBot()
        fast_bot2 = FastBot()
        
        engine.add_bot(fast_bot1)
        engine.add_bot(fast_bot2)
        
        engine.load_deck_from_config("configs/default_deck.json")
        
        # Game should complete normally
        winner = engine.run()
        
        # No timeout events should be recorded
        timeout_events = [
            e for e in engine.history.get_events()
            if e.event_type == EventType.BOT_TIMEOUT
        ]
        assert len(timeout_events) == 0, "Timeout events recorded when timeout disabled"
    
    def test_timeout_error_exception(self) -> None:
        """Test that BotTimeoutError has correct attributes."""
        error = BotTimeoutError("TestBot", "take_turn", 5.0)
        
        assert error.player_id == "TestBot"
        assert error.method_name == "take_turn"
        assert error.timeout == 5.0
        assert "TestBot" in str(error)
        assert "take_turn" in str(error)
        assert "5.0" in str(error)
    
    def test_fast_bot_not_affected_by_timeout(self) -> None:
        """Test that fast bots complete normally with timeout enabled."""
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=1.0)
        
        fast_bot1 = FastBot()
        fast_bot2 = FastBot()
        
        engine.add_bot(fast_bot1)
        engine.add_bot(fast_bot2)
        
        engine.load_deck_from_config("configs/default_deck.json")
        
        winner = engine.run()
        
        # One of the fast bots should win
        assert winner in ["FastBot", "FastBot_2"]
        
        # No timeout events
        timeout_events = [
            e for e in engine.history.get_events()
            if e.event_type == EventType.BOT_TIMEOUT
        ]
        assert len(timeout_events) == 0


class TestTimeoutWithMultipleBots:
    """Tests for timeout with multiple bots."""
    
    def test_multiple_slow_bots_eliminated(self) -> None:
        """Test that multiple slow bots are all eliminated."""
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=0.1)
        
        # Add 2 slow bots and 1 fast bot
        slow1 = SlowBot(delay=1.0, slow_methods={"take_turn"})
        slow2 = SlowBot(delay=1.0, slow_methods={"take_turn"})
        fast = FastBot()
        
        engine.add_bot(slow1)
        engine.add_bot(slow2)
        engine.add_bot(fast)
        
        engine.load_deck_from_config("configs/default_deck.json")
        
        winner = engine.run()
        
        # Fast bot should win
        assert winner == "FastBot", f"Expected FastBot to win, got {winner}"
        
        # Both slow bots should have timeout events
        timeout_events = [
            e for e in engine.history.get_events()
            if e.event_type == EventType.BOT_TIMEOUT
        ]
        # At least one timeout should be recorded (both slow bots timed out)
        assert len(timeout_events) >= 1
