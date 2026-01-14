"""
Test bot that deliberately times out to verify the timeout mechanism.
This bot should NOT be used in normal games - it's only for testing!
"""

import time

from game.bots.base import (
    Action,
    Bot,
    DrawCardAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent


class SlowBot(Bot):
    """A bot that deliberately takes too long, for testing timeout handling."""
    
    def __init__(self, delay: float = 10.0) -> None:
        """Initialize with configurable delay (default 10 seconds)."""
        self._delay = delay
    
    @property
    def name(self) -> str:
        return "SlowBot"
    
    def take_turn(self, view: BotView) -> Action:
        """Deliberately timeout on take_turn."""
        time.sleep(self._delay)
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """Fast event handling (no timeout here)."""
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """Don't react."""
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """Quick defuse position choice."""
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """Quick card choice."""
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        """Say last words quickly."""
        view.say("I was too slow...")
