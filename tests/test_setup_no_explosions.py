"""
Test that Exploding Kittens are not in the deck during initial hand dealing.

According to Exploding Kittens rules, Exploding Kittens should be shuffled
into the deck AFTER initial hands are dealt, not before.
"""

import pytest

from game.engine import GameEngine
from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import EventType, GameEvent


class SimpleBot(Bot):
    """A simple bot that always draws."""
    
    def __init__(self, name: str) -> None:
        self._name: str = name
    
    @property
    def name(self) -> str:
        return self._name
    
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


class TestSetupNoExplosions:
    """Tests that players cannot explode during initial hand dealing."""
    
    def test_no_exploding_kittens_during_initial_deal(self) -> None:
        """
        Players should not draw Exploding Kittens during initial hand dealing.
        
        Per Exploding Kittens rules, Exploding Kittens are shuffled into the
        deck AFTER initial hands are dealt.
        """
        engine: GameEngine = GameEngine(seed=42)
        
        # Add 5 players
        for i in range(5):
            engine.add_bot(SimpleBot(f"Bot{i}"))
        
        # Use default deck which includes Exploding Kittens
        engine.create_deck({
            "ExplodingKittenCard": 4,
            "DefuseCard": 6,
            "TacoCatCard": 40,
        })
        
        # This is the critical call - setup should not cause explosions
        engine.setup_game(initial_hand_size=7)
        
        # Check that no EXPLODING_KITTEN_DRAWN events occurred during setup
        explosion_events = engine.history.get_events_by_type(EventType.EXPLODING_KITTEN_DRAWN)
        
        assert len(explosion_events) == 0, \
            "Players should not draw Exploding Kittens during initial setup"
        
        # All 5 players should still be alive after setup
        alive_players = engine._state.get_alive_players()
        assert len(alive_players) == 5, \
            f"All 5 players should be alive after setup, got {len(alive_players)}"
    
    def test_exploding_kittens_added_after_setup(self) -> None:
        """
        Exploding Kittens should be in the deck AFTER setup is complete.
        
        This verifies that while Exploding Kittens are not dealt during setup,
        they are properly shuffled into the deck for the actual game.
        """
        engine: GameEngine = GameEngine(seed=42)
        
        for i in range(3):
            engine.add_bot(SimpleBot(f"Bot{i}"))
        
        engine.create_deck({
            "ExplodingKittenCard": 2,  # 2 exploding kittens
            "DefuseCard": 4,
            "TacoCatCard": 30,
        })
        
        engine.setup_game(initial_hand_size=5)
        
        # After setup, the draw pile should contain the Exploding Kittens
        draw_pile = engine._state.draw_pile
        exploding_kitten_count = sum(
            1 for card in draw_pile 
            if card.card_type == "ExplodingKittenCard"
        )
        
        # Per rules: number of Exploding Kittens = num_players - 1
        # But for this test, we're checking the implementation shuffles them in
        assert exploding_kitten_count >= 1, \
            "Exploding Kittens should be in the draw pile after setup"
