"""
Tests for the bot system.

These tests verify bot interface, BotView safety (anti-cheat),
and dynamic bot loading.
"""

import pytest
import tempfile
from pathlib import Path

from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
    PassAction,
    PlayCardAction,
)
from game.bots.view import BotView
from game.bots.loader import BotLoader
from game.cards.action_cards import SkipCard, NopeCard
from game.cards.cat_cards import TacoCatCard
from game.history import GameEvent, EventType


def create_test_view_with_cards() -> BotView:
    """Create a BotView with some cards in hand for testing."""
    skip_card = SkipCard()
    nope_card = NopeCard()
    combo1 = TacoCatCard()
    combo2 = TacoCatCard()
    
    return BotView(
        my_id="test_player",
        my_hand=(skip_card, nope_card, combo1, combo2),
        my_turns_remaining=1,
        discard_pile=(),
        draw_pile_count=20,
        other_players=("player2", "player3"),
        other_player_card_counts={"player2": 7, "player3": 5},
        current_player="test_player",
        turn_order=("test_player", "player2", "player3"),
        is_my_turn=True,
        recent_events=(),
    )


class TestBotView:
    """Tests for the BotView class (anti-cheat)."""
    
    def test_view_is_immutable(self) -> None:
        """BotView should be immutable (frozen dataclass)."""
        view: BotView = create_test_view_with_cards()
        
        with pytest.raises(Exception):  # FrozenInstanceError
            view.my_id = "hacker"  # type: ignore[misc]
    
    def test_hand_is_immutable(self) -> None:
        """The hand tuple should be immutable."""
        view: BotView = create_test_view_with_cards()
        
        # Tuples are immutable, so we can't append
        assert isinstance(view.my_hand, tuple)
    
    def test_other_players_only_shows_ids(self) -> None:
        """Bots should only see other players' IDs, not their cards."""
        view: BotView = create_test_view_with_cards()
        
        # other_players is just IDs
        assert view.other_players == ("player2", "player3")
        
        # other_player_card_counts is just counts, not actual cards
        assert view.other_player_card_counts["player2"] == 7
    
    def test_draw_pile_only_shows_count(self) -> None:
        """Bots should only see draw pile count, not contents."""
        view: BotView = create_test_view_with_cards()
        
        # Only count is available
        assert view.draw_pile_count == 20
        
        # There's no way to see actual cards
        # (the attribute doesn't exist)
        assert not hasattr(view, "draw_pile")
    
    def test_get_cards_of_type(self) -> None:
        """get_cards_of_type should filter cards correctly."""
        view: BotView = create_test_view_with_cards()
        
        combo_cards = view.get_cards_of_type("TacoCatCard")
        
        assert len(combo_cards) == 2
    
    def test_has_card_type(self) -> None:
        """has_card_type should check for card presence."""
        view: BotView = create_test_view_with_cards()
        
        assert view.has_card_type("SkipCard") is True
        assert view.has_card_type("AttackCard") is False
    
    def test_get_playable_cards(self) -> None:
        """get_playable_cards should return only playable cards."""
        view: BotView = create_test_view_with_cards()
        
        playable = view.get_playable_cards()
        
        # All 4 cards are playable on own turn:
        # Skip, Nope (can play, does nothing), and both TacoCat cards
        assert len(playable) == 4
        playable_types = [c.card_type for c in playable]
        assert "SkipCard" in playable_types
        assert "NopeCard" in playable_types
        assert "TacoCatCard" in playable_types
    
    def test_get_reaction_cards(self) -> None:
        """get_reaction_cards should return only reaction cards."""
        view: BotView = create_test_view_with_cards()
        
        reactions = view.get_reaction_cards()
        
        # Only Nope is a reaction card
        assert len(reactions) == 1
        assert reactions[0].card_type == "NopeCard"
    
    def test_can_play_combo(self) -> None:
        """can_play_combo should check for valid combos."""
        view: BotView = create_test_view_with_cards()
        
        # We have 2 TacoCatCards
        assert view.can_play_combo("TacoCatCard", required_count=2) is True
        assert view.can_play_combo("TacoCatCard", required_count=3) is False
        
        # We only have 1 SkipCard (and it can't combo)
        assert view.can_play_combo("SkipCard", required_count=2) is False


class TestBotLoader:
    """Tests for dynamic bot loading."""
    
    def test_load_from_nonexistent_directory_raises(self) -> None:
        """Loading from a non-existent directory should raise."""
        loader: BotLoader = BotLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_from_directory("/nonexistent/directory")
    
    def test_load_from_empty_directory(self) -> None:
        """Loading from an empty directory should return empty list."""
        loader: BotLoader = BotLoader()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            bots = loader.load_from_directory(tmpdir)
            assert bots == []
    
    def test_load_simple_bot(self) -> None:
        """Loading a simple bot should work."""
        loader: BotLoader = BotLoader()
        
        bot_code: str = '''
from game.bots.base import Bot, Action, DrawCardAction
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent

class SimpleBot(Bot):
    @property
    def name(self) -> str:
        return "SimpleBot"
    
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
'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            bot_file: Path = Path(tmpdir) / "simple_bot.py"
            bot_file.write_text(bot_code)
            
            bots = loader.load_from_directory(tmpdir)
            
            assert len(bots) == 1
            assert bots[0].name == "SimpleBot"
    
    def test_skips_files_starting_with_underscore(self) -> None:
        """Files starting with _ should be skipped."""
        loader: BotLoader = BotLoader()
        
        bot_code: str = '''
from game.bots.base import Bot, Action, DrawCardAction
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent

class HiddenBot(Bot):
    @property
    def name(self) -> str:
        return "HiddenBot"
    
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
'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an __init__.py which should be skipped
            init_file: Path = Path(tmpdir) / "__init__.py"
            init_file.write_text("")
            
            # Create a _private.py which should be skipped
            private_file: Path = Path(tmpdir) / "_private.py"
            private_file.write_text(bot_code)
            
            bots = loader.load_from_directory(tmpdir)
            
            assert len(bots) == 0
