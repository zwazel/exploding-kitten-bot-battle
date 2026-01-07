"""
Test that a single _run_turn call results in exactly one card draw.

This test catches the bug where bots draw multiple cards per turn instead
of ending their turn after the first draw.
"""

import pytest
from typing import Any

from game.engine import GameEngine
from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
    PlayCardAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import EventType, GameEvent


class DrawCountingBot(Bot):
    """
    A bot that tracks how many times take_turn is called per turn
    and always chooses to draw.
    """
    
    def __init__(self, name: str) -> None:
        self._name: str = name
        self.take_turn_call_count: int = 0
    
    @property
    def name(self) -> str:
        return self._name
    
    def take_turn(self, view: BotView) -> Action:
        self.take_turn_call_count += 1
        # Always immediately draw to end the turn
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]


class TestSingleDrawPerTurn:
    """Tests that a single turn results in exactly one card draw."""
    
    def test_run_turn_draws_exactly_one_card(self) -> None:
        """
        A single _run_turn call should result in exactly one card drawn.
        
        This test catches the bug where bots draw multiple cards in a
        single turn instead of ending their turn after the first draw.
        """
        engine: GameEngine = GameEngine(seed=42)
        
        bot1 = DrawCountingBot("Bot1")
        bot2 = DrawCountingBot("Bot2")
        
        engine.add_bot(bot1)
        engine.add_bot(bot2)
        
        # Create a safe deck (no exploding kittens)
        engine.create_deck({
            "TacoCatCard": 30,
            "SkipCard": 10,
        })
        engine.setup_game(initial_hand_size=5)
        
        # Count cards drawn during setup (5 per player = 10 total)
        setup_draw_events = engine.history.get_events_by_type(EventType.CARD_DRAWN)
        setup_draw_count = len(setup_draw_events)
        
        # Force turn order to start with Bot1
        engine._turn_manager._turn_order = ["Bot1", "Bot2"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"Bot1": 1, "Bot2": 1}
        engine._state._turn_order = ["Bot1", "Bot2"]
        engine._state._current_player_index = 0
        
        # Reset bot's call counter
        bot1.take_turn_call_count = 0
        
        # Run a single turn for Bot1
        engine._run_turn("Bot1")
        
        # Check how many times take_turn was called
        assert bot1.take_turn_call_count == 1, \
            f"take_turn should be called exactly once, was called {bot1.take_turn_call_count} times"
        
        # Check how many cards were drawn during this turn
        all_draw_events = engine.history.get_events_by_type(EventType.CARD_DRAWN)
        turn_draw_count = len(all_draw_events) - setup_draw_count
        
        assert turn_draw_count == 1, \
            f"Expected exactly 1 card drawn during turn, got {turn_draw_count}"

